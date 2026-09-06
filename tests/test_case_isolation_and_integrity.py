import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import select

from app.models.entities import (
    Case, Evidence, Observation, CandidateEntity, Hypothesis, GapConflict, Report, User
)
from app.models.enums import (
    CaseType, CaseStatus, EvidenceType, Department, ObservationType,
    HypothesisStatus, ClaimStrength, GapConflictType, Significance
)
from app.department_engines.framework.base import (
    EngineContext, EngineExecutionRecord, EngineExecutionResult, ExecutionMode
)
from app.department_engines.framework.input_resolver import input_resolver, ScopeViolationError
from app.department_engines.dispatcher import run_case_analysis
from app.department_engines.framework.registry import engine_registry
from app.reports.service import generate_case_report
from app.reconstruction.final_verification_engine import (
    final_verification_engine, FinalVerificationDetermination
)


# ===========================================================================
# 1. Regression Test: Case A and Case B with similar evidence names -> zero cross-case leakage
# ===========================================================================
@pytest.mark.asyncio
async def test_case_a_and_case_b_zero_cross_case_leakage(db_session, seed_users):
    """
    Case A and Case B with identically-named evidence items (e.g. cctv_depot_bay4_exterior.mp4)
    must remain mathematically isolated with zero cross-case leakage.
    """
    user = seed_users["investigator"]

    case_a = Case(
        case_number="CASE-2026-AAA",
        title="Depot Incident Case A",
        case_type=CaseType.THEFT,
        created_by=user.id,
        current_version=1
    )
    case_b = Case(
        case_number="CASE-2026-BBB",
        title="Depot Incident Case B",
        case_type=CaseType.THEFT,
        created_by=user.id,
        current_version=1
    )
    db_session.add_all([case_a, case_b])
    await db_session.flush()

    ev_a = Evidence(
        case_id=case_a.id,
        evidence_type=EvidenceType.CCTV,
        original_filename="cctv_depot_bay4_exterior.mp4",
        storage_key="/store/case_a/cctv_depot_bay4_exterior.mp4",
        file_size_bytes=2048,
        sha256_hash="hash_a",
        uploaded_by=user.id
    )
    ev_b = Evidence(
        case_id=case_b.id,
        evidence_type=EvidenceType.CCTV,
        original_filename="cctv_depot_bay4_exterior.mp4",
        storage_key="/store/case_b/cctv_depot_bay4_exterior.mp4",
        file_size_bytes=2048,
        sha256_hash="hash_b",
        uploaded_by=user.id
    )
    db_session.add_all([ev_a, ev_b])
    await db_session.commit()

    # Verify input_resolver strictly isolates evidence
    evs_a = await input_resolver.resolve_evidence(db_session, case_a.id)
    evs_b = await input_resolver.resolve_evidence(db_session, case_b.id)

    assert len(evs_a) == 1 and evs_a[0].id == ev_a.id
    assert len(evs_b) == 1 and evs_b[0].id == ev_b.id
    assert evs_a[0].id != evs_b[0].id

    # Create an observation for Case A
    obs_a = Observation(
        case_id=case_a.id,
        evidence_id=ev_a.id,
        analysis_version=1,
        department=Department.INVESTIGATION,
        observation_type=ObservationType.PERSON_DETECTED,
        raw_data={"track_id": "TRK_CASE_A"},
        model_name="I03",
        model_version="1.0.0"
    )
    db_session.add(obs_a)
    await db_session.commit()

    # Verify Case B resolves 0 observations
    obs_b_list = await input_resolver.resolve_observations(db_session, case_b.id, analysis_version=1)
    assert len(obs_b_list) == 0

    # Verify input_resolver raises ScopeViolationError if Case A record is in Case B context
    foreign_rec = EngineExecutionRecord(
        case_id=case_a.id,
        analysis_version=1,
        engine_id="I03",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.MODEL,
        outputs=[{"track_id": "TRK_CASE_A"}]
    )
    ctx_b = EngineContext(case_id=case_b.id, analysis_version=1)
    ctx_b.prior_results["I03"] = foreign_rec

    with pytest.raises(ScopeViolationError) as excinfo:
        input_resolver.filter_prior_results_for_engine(ctx_b, case_b.id, target_analysis_version=1)
    assert "Cross-case contamination blocked" in str(excinfo.value)


# ===========================================================================
# 2. Regression Test: Case A version 1 vs version 2 -> v2 never consumes v1 outputs
# ===========================================================================
@pytest.mark.asyncio
async def test_version_isolation_v2_never_consumes_v1(db_session, seed_users):
    """
    When an analysis run occurs for analysis_version=2, it must never consume
    records or outputs belonging to analysis_version=1.
    """
    user = seed_users["investigator"]
    case = Case(
        case_number="CASE-VER-001",
        title="Version Isolation Case",
        case_type=CaseType.THEFT,
        created_by=user.id,
        current_version=1
    )
    db_session.add(case)
    await db_session.flush()

    # Seed v1 observation
    ev = Evidence(
        case_id=case.id,
        evidence_type=EvidenceType.CCTV,
        original_filename="vault_hallway.mp4",
        storage_key="/store/vault_hallway.mp4",
        file_size_bytes=1024,
        sha256_hash="hash_vh",
        uploaded_by=user.id
    )
    db_session.add(ev)
    await db_session.flush()

    obs_v1 = Observation(
        case_id=case.id,
        evidence_id=ev.id,
        analysis_version=1,
        department=Department.INVESTIGATION,
        observation_type=ObservationType.PERSON_DETECTED,
        raw_data={"event": "v1 observation"},
        model_name="I03",
        model_version="1.0.0"
    )
    db_session.add(obs_v1)
    await db_session.commit()

    # Resolving observations for v2 must return empty
    obs_v2 = await input_resolver.resolve_observations(db_session, case.id, analysis_version=2)
    assert len(obs_v2) == 0

    # In-memory context isolation check:
    # Context configured for version 2 attempting to consume version 1 record
    stale_rec = EngineExecutionRecord(
        case_id=case.id,
        analysis_version=1,
        engine_id="X02",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC,
        outputs=[{"event_id": "TL_01", "timestamp": "2026-09-06T10:00:00Z"}]
    )
    ctx_v2 = EngineContext(case_id=case.id, analysis_version=2)
    ctx_v2.prior_results["X02"] = stale_rec

    with pytest.raises(ScopeViolationError) as excinfo:
        input_resolver.filter_prior_results_for_engine(ctx_v2, case.id, target_analysis_version=2)
    assert "Stale-version contamination blocked" in str(excinfo.value)


# ===========================================================================
# 3. Regression Test: X03 reports 3 correlated events but X06 records 2 -> hard verification failure
# ===========================================================================
def test_x03_x06_correlation_count_mismatch_hard_verification_failure():
    """
    If X03 produced 3 correlated events, but X06 reported 2 in its evaluation payload,
    Final Verification Engine must flag CORRELATION_COUNT_MISMATCH and declare REANALYSIS_REQUIRED.
    """
    case_id = "case_corr_mismatch"
    analysis_version = 1

    # X03 record with 3 valid correlations
    x03_outputs = [
        {"correlation_id": "CORR_01", "correlation_type": "SPATIO_TEMPORAL_COINCIDENCE", "case_id": case_id, "analysis_version": analysis_version},
        {"correlation_id": "CORR_02", "correlation_type": "SPATIAL_COINCIDENCE", "case_id": case_id, "analysis_version": analysis_version},
        {"correlation_id": "CORR_03", "correlation_type": "MULTI_SENSOR_SYNC", "case_id": case_id, "analysis_version": analysis_version},
    ]
    x03_rec = EngineExecutionRecord(
        case_id=case_id,
        analysis_version=analysis_version,
        engine_id="X03",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC,
        outputs=x03_outputs
    )

    # X06 record that inconsistently reports 2 correlated events
    x06_outputs = [{
        "case_id": case_id,
        "analysis_version": analysis_version,
        "sufficiency_rating": "SUFFICIENT_FOR_RECONSTRUCTION",
        "proceed_to_reconstruction": True,
        "correlated_event_count": 2, # Inconsistent! Expected 3
        "source_event_count": 3,
        "decision_basis": ["2 correlated events (3 source-local events)"]
    }]
    x06_rec = EngineExecutionRecord(
        case_id=case_id,
        analysis_version=analysis_version,
        engine_id="X06",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.HYBRID,
        outputs=x06_outputs
    )

    engine_outputs = {
        "X03": x03_rec,
        "X06": x06_rec
    }

    result = final_verification_engine.verify(
        engine_outputs=engine_outputs,
        valid_evidence_ids=set(),
        case_id=case_id,
        analysis_version=analysis_version
    )

    assert result.determination in (FinalVerificationDetermination.REANALYSIS_REQUIRED, FinalVerificationDetermination.HARD_INTEGRITY_VIOLATION)
    assert "CORRELATION_COUNT_MISMATCH" in result.checks_failed
    matching_issues = [i for i in result.issues if i.check_id == "CORRELATION_COUNT_MISMATCH"]
    assert len(matching_issues) == 1
    assert "Accounting contradiction" in matching_issues[0].description
    assert "X06 recorded 2 correlated events, but X03 produced 3" in matching_issues[0].description


# ===========================================================================
# 4. Regression Test: R01 references P1 while X01 has no P1 -> hard rejection
# ===========================================================================
def test_r01_references_unknown_entity_hard_rejection():
    """
    If R01 references candidate entity 'P1' (or 'ENTITY_P1') when X01 generated
    no such entity, Final Verification Engine must flag UNKNOWN_ENTITY_REFERENCE
    and reject the analytical output.
    """
    case_id = "case_unknown_entity"
    analysis_version = 1

    # X01 only produced an item entity (no person P1)
    x01_rec = EngineExecutionRecord(
        case_id=case_id,
        analysis_version=analysis_version,
        engine_id="X01",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.HYBRID,
        outputs=[{
            "entity_id": "ENTITY_ITEM1",
            "entity_type": "ITEM",
            "candidate_label": "High-Value Item",
            "case_id": case_id,
            "analysis_version": analysis_version
        }]
    )

    # R01 improperly assumes P1 exists
    r01_rec = EngineExecutionRecord(
        case_id=case_id,
        analysis_version=analysis_version,
        engine_id="R01",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.HYBRID,
        outputs=[{
            "hypothesis_id": "HYP_01",
            "hypothesis_title": "Primary Scenario",
            "narrative": "Subject identified as candidate entity P1 removed stock.",
            "entity_link_dependence": ["ENTITY_P1"], # Unknown entity!
            "supporting_evidence_citations": ["Ex 01"]
        }]
    )

    engine_outputs = {
        "X01": x01_rec,
        "R01": r01_rec
    }

    result = final_verification_engine.verify(
        engine_outputs=engine_outputs,
        valid_evidence_ids={"00000000-0000-0000-0000-000000000001"},
        case_id=case_id,
        analysis_version=analysis_version
    )

    assert result.determination in (FinalVerificationDetermination.REANALYSIS_REQUIRED, FinalVerificationDetermination.HARD_INTEGRITY_VIOLATION)
    assert "UNKNOWN_ENTITY_REFERENCE" in result.checks_failed
    matching_issues = [i for i in result.issues if i.check_id == "UNKNOWN_ENTITY_REFERENCE"]
    assert len(matching_issues) >= 1
    assert any("ENTITY_P1" in i.description or "P1" in i.description for i in matching_issues)


# ===========================================================================
# 5. Regression Test: Old hypothesis in database -> new report cannot inherit it
# ===========================================================================
@pytest.mark.asyncio
async def test_old_hypothesis_not_inherited_by_new_report(db_session, seed_users):
    """
    If a hypothesis from analysis_version=1 exists in the database, generating
    a report for analysis_version=2 must not inherit or include the old hypothesis.
    """
    user = seed_users["investigator"]
    case = Case(
        case_number="CASE-HYP-ISOLATE",
        title="Hypothesis Isolation Case",
        case_type=CaseType.THEFT,
        created_by=user.id,
        current_version=2
    )
    db_session.add(case)
    await db_session.flush()

    # Old v1 hypothesis
    old_hyp = Hypothesis(
        case_id=case.id,
        analysis_version=1,
        label="Legacy Stale Hypothesis from v1",
        description="This was an old preliminary hypothesis that should not leak into v2.",
        status=HypothesisStatus.DRAFT,
        overall_strength=ClaimStrength.MODERATE
    )
    # New v2 hypothesis
    new_hyp = Hypothesis(
        case_id=case.id,
        analysis_version=2,
        label="Defensible v2 Hypothesis",
        description="Active hypothesis generated for version 2.",
        status=HypothesisStatus.DRAFT,
        overall_strength=ClaimStrength.STRONG
    )
    db_session.add_all([old_hyp, new_hyp])
    await db_session.commit()

    # Generate report for analysis_version=2
    report = await generate_case_report(db_session, case, user, analysis_version=2)

    assert report.analysis_version == 2
    reconstructed_hyps = report.report_data.get("reconstructed_hypotheses", [])
    hyp_labels = [h.get("label") for h in reconstructed_hyps]

    assert "Defensible v2 Hypothesis" in hyp_labels
    assert "Legacy Stale Hypothesis from v1" not in hyp_labels


# ===========================================================================
# 6. Regression Test: Historical knowledge influence planning only, not evidence
# ===========================================================================
def test_historical_knowledge_cannot_appear_as_current_case_evidence():
    """
    If historical knowledge is cited as evidence in an analytical output
    (or foreign exhibit referenced), FVE must flag CHECK_10_CONTAMINATION
    or CROSS_CASE_EVIDENCE_REFERENCE and declare REANALYSIS_REQUIRED.
    """
    case_id = "case_historical_guard"
    analysis_version = 1
    valid_exhibit_id = "11111111-1111-1111-1111-111111111111"
    foreign_exhibit_id = "99999999-9999-9999-9999-999999999999"

    # Engine citing foreign exhibit and historical case language
    rec = EngineExecutionRecord(
        case_id=case_id,
        analysis_version=analysis_version,
        engine_id="R01",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.HYBRID,
        outputs=[{
            "hypothesis_id": "HYP_01",
            "hypothesis_title": "Contaminated Hypothesis",
            "narrative": "Based on prior knowledge and similar past cases, subject acted identically.",
            "supporting_evidence_citations": [foreign_exhibit_id],
            "entity_link_dependence": []
        }]
    )

    result = final_verification_engine.verify(
        engine_outputs={"R01": rec},
        valid_evidence_ids={valid_exhibit_id},
        case_id=case_id,
        analysis_version=analysis_version
    )

    assert result.determination in (FinalVerificationDetermination.REANALYSIS_REQUIRED, FinalVerificationDetermination.HARD_INTEGRITY_VIOLATION)
    # Must flag contamination and/or cross-case reference
    failed_checks = set(result.checks_failed)
    assert ("CHECK_10_CONTAMINATION" in failed_checks) or ("CROSS_CASE_EVIDENCE_REFERENCE" in failed_checks)
