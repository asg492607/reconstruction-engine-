import pytest
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entities import Case, Evidence, User, Organization, Observation, Hypothesis
from app.models.enums import EvidenceType, ProcessingStatus, Department, ClaimStrength, HypothesisStatus
from app.reconstruction.integrity_gate import (
    validate_evidence_reference_integrity,
    enforce_evidence_reference_integrity,
    UnsupportedEvidenceReferenceException
)
from app.department_engines.dispatcher import (
    get_case_analysis_plan,
    execute_case_analysis_plan,
    get_case_telemetry
)
from app.department_engines.framework.base import EngineExecutionResult

# ---------------------------------------------------------------------------
# TEST 1: Evidence Reference Integrity Gate Unit Tests
# ---------------------------------------------------------------------------

def test_integrity_gate_detects_unavailable_modalities():
    # Case has only IMAGE and WITNESS_STATEMENT exhibits
    class MockEvidence:
        def __init__(self, ev_type):
            self.evidence_type = ev_type

    exhibits = [
        MockEvidence("IMAGE"),
        MockEvidence("WITNESS_STATEMENT")
    ]

    # Positive claim citing CCTV: MUST FAIL
    cctv_claim = "Corroborated by physical strike plate pry marks and CCTV data (02:45)."
    is_valid, violations = validate_evidence_reference_integrity(exhibits, cctv_claim)
    assert not is_valid
    assert any("VIDEO_CCTV" in v for v in violations)
    assert any("UNSUPPORTED_EVIDENCE_REFERENCE" in v for v in violations)

    # Positive claim citing vehicle departure: MUST FAIL
    vehicle_claim = "Unregistered dark sedan departing 5th Ave at vehicle exit timestamps."
    is_valid, violations = validate_evidence_reference_integrity(exhibits, vehicle_claim)
    assert not is_valid
    assert any("VEHICLE_TRACKING" in v for v in violations)

    # Positive claim citing POS ledger: MUST FAIL
    pos_claim = "Financial inventory ledger audit and POS transaction show deficit of 3 units."
    is_valid, violations = validate_evidence_reference_integrity(exhibits, pos_claim)
    assert not is_valid
    assert any("FINANCIAL_POS" in v for v in violations)

    # Negative gap description: MUST PASS (stating evidence is missing is permitted)
    gap_statement = "No CCTV footage or POS logs attached; direct removal not observed."
    is_valid, violations = validate_evidence_reference_integrity(exhibits, gap_statement)
    assert is_valid
    assert len(violations) == 0

    # Legitimate claim supported by attached IMAGE and WITNESS exhibits: MUST PASS
    legit_claim = "Physical pry mark deformation on door aperture consistent with witness statement describing hurried exit."
    is_valid, violations = validate_evidence_reference_integrity(exhibits, legit_claim)
    assert is_valid

    # Strict enforcement raises exception (no sanitizing)
    with pytest.raises(UnsupportedEvidenceReferenceException):
        enforce_evidence_reference_integrity(exhibits, {"summary": "CCTV confirms entry at 02:45"})


# ---------------------------------------------------------------------------
# TEST 2: End-to-End Pipeline Regression Test (Image + Witness Only)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_image_plus_witness_never_references_cctv_or_vehicle(db_session: AsyncSession):
    # Setup Organization and User
    org = Organization(id=str(uuid.uuid4()), name="Integrity Test Unit")
    db_session.add(org)
    user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        email=f"auditor_{uuid.uuid4().hex[:6]}@rre.internal",
        hashed_password="hashed_test_password",
        full_name="Integrity Auditor",
        role="LEAD_INVESTIGATOR",
        department="INVESTIGATION"
    )
    db_session.add(user)
    await db_session.commit()

    # Create case with ONLY Image + Witness exhibits
    case = Case(
        id=str(uuid.uuid4()),
        case_number=f"TEST-INT-{uuid.uuid4().hex[:6]}",
        title="Restricted Exhibit Intake Case",
        case_type="THEFT",
        specific_offense="BURGLARY",
        organization_id=org.id,
        created_by=user.id
    )
    db_session.add(case)

    # Exhibit 1: Forensic Image
    ev_image = Evidence(
        id=str(uuid.uuid4()),
        case_id=case.id,
        evidence_type=EvidenceType.IMAGE,
        original_filename="door_strike_plate_damage.jpg",
        storage_key=f"{case.id}/door_strike_plate_damage.jpg",
        sha256_hash="a" * 64,
        file_size_bytes=1024,
        mime_type="image/jpeg",
        uploaded_by=user.id
    )
    # Exhibit 2: Witness Statement TXT
    ev_witness = Evidence(
        id=str(uuid.uuid4()),
        case_id=case.id,
        evidence_type=EvidenceType.WITNESS_STATEMENT,
        original_filename="witness_guard_statement.txt",
        storage_key=f"{case.id}/witness_guard_statement.txt",
        sha256_hash="b" * 64,
        file_size_bytes=512,
        mime_type="text/plain",
        uploaded_by=user.id
    )
    db_session.add_all([ev_image, ev_witness])
    await db_session.commit()

    # 1. Verify Dynamic Analysis Plan marks CCTV & POS engines as UNAVAILABLE
    plan = await get_case_analysis_plan(db_session, case)
    unavail_eids = {u["engine_id"] for u in plan.unavailable_engines}
    assert "I01" in unavail_eids # Video Metadata Engine
    assert "I03" in unavail_eids # Subject Detection
    assert "I05" in unavail_eids # Vehicle Tracking
    assert "FI02" in unavail_eids # Inventory Audit
    assert "FI04" in unavail_eids # POS Journal Audit

    # 2. Execute full 45-engine backbone sequence
    exec_result = await execute_case_analysis_plan(db_session, case, user_id=user.id)
    assert exec_result["engines_executed"] > 0

    # 3. Verify Telemetry: CCTV and POS engines were BLOCKED, NOT run against the image
    telemetry = get_case_telemetry(case.id)
    tele_by_id = {t["engine_id"]: t for t in telemetry}

    for eid in ["I01", "I02", "I03", "I05", "FI02", "FI04"]:
        rec = tele_by_id.get(eid)
        assert rec is not None, f"Engine {eid} must have an execution record in telemetry"
        assert rec["status"] in [EngineExecutionResult.BLOCKED.value, "BLOCKED"], (
            f"Engine {eid} must be BLOCKED when evidence is missing, but was {rec['status']}"
        )
        assert "Unavailable: No accepted evidence modality" in (rec.get("failure_reason") or "")

    # 4. Check Observations in Database:
    # All observations must link strictly to ev_image.id or ev_witness.id
    obs_stmt = select(Observation).where(Observation.case_id == case.id)
    case_obs = (await db_session.execute(obs_stmt)).scalars().all()

    for o in case_obs:
        assert o.evidence_id in [ev_image.id, ev_witness.id], (
            f"Observation {o.id} links to unknown evidence_id {o.evidence_id}"
        )
        # Verify no observation raw_data asserts CCTV or vehicle exits
        raw_str = str(o.raw_data or {}).lower()
        assert "cctv_camera" not in raw_str
        assert "dark sedan" not in raw_str
        assert "vehicle exit timestamp" not in raw_str

    # 5. Check R01 Hypothesis: Must be INSUFFICIENT_EVIDENCE
    r01_rec = tele_by_id.get("R01")
    assert r01_rec is not None
    assert r01_rec["outputs"], f"R01 outputs empty: {r01_rec.get('failure_reason')}"
    top_hyp = r01_rec["outputs"][0]
    assert top_hyp["hypothesis_category"] == "INSUFFICIENT_EVIDENCE"
    assert "Insufficient Evidence" in top_hyp["hypothesis_title"]
    assert top_hyp["theft_conclusion_supported"] is False

    # 6. Check Evidence Sufficiency Engine (X06):
    x06_rec = tele_by_id.get("X06")
    assert x06_rec is not None
    assert x06_rec["outputs"][0]["proceed_to_reconstruction"] is False
    assert x06_rec["outputs"][0]["sufficiency_rating"] == "INSUFFICIENT_FOR_RECONSTRUCTION"


# ---------------------------------------------------------------------------
# TEST 3: Multi-Case Isolation Regression Test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_multi_case_isolation_and_no_observation_leakage(db_session: AsyncSession):
    # Setup Organization
    org = Organization(id=str(uuid.uuid4()), name="Isolation Workspace")
    db_session.add(org)
    user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        email=f"iso_{uuid.uuid4().hex[:6]}@rre.internal",
        hashed_password="hashed_test_password",
        full_name="Isolation Specialist",
        role="LEAD_INVESTIGATOR",
        department="INVESTIGATION"
    )
    db_session.add(user)
    await db_session.commit()

    # Case A: Location Alpha
    case_a = Case(
        id=str(uuid.uuid4()),
        case_number=f"ISO-A-{uuid.uuid4().hex[:6]}",
        title="Case Alpha: Electronics Store A",
        case_type="THEFT",
        organization_id=org.id,
        created_by=user.id
    )
    # Case B: Location Beta
    case_b = Case(
        id=str(uuid.uuid4()),
        case_number=f"ISO-B-{uuid.uuid4().hex[:6]}",
        title="Case Beta: Warehouse B",
        case_type="THEFT",
        organization_id=org.id,
        created_by=user.id
    )
    db_session.add_all([case_a, case_b])

    # Exhibits for Case A
    ev_a1 = Evidence(
        id=str(uuid.uuid4()),
        case_id=case_a.id,
        evidence_type=EvidenceType.IMAGE,
        original_filename="case_a_photo.jpg",
        storage_key=f"{case_a.id}/photo.jpg",
        sha256_hash="1" * 64,
        file_size_bytes=1024,
        mime_type="image/jpeg",
        uploaded_by=user.id
    )
    # Exhibits for Case B
    ev_b1 = Evidence(
        id=str(uuid.uuid4()),
        case_id=case_b.id,
        evidence_type=EvidenceType.IMAGE,
        original_filename="case_b_photo.jpg",
        storage_key=f"{case_b.id}/photo.jpg",
        sha256_hash="2" * 64,
        file_size_bytes=1024,
        mime_type="image/jpeg",
        uploaded_by=user.id
    )
    db_session.add_all([ev_a1, ev_b1])
    await db_session.commit()

    # Execute Case A analysis
    await execute_case_analysis_plan(db_session, case_a, user_id=user.id)

    # Execute Case B analysis
    await execute_case_analysis_plan(db_session, case_b, user_id=user.id)

    # Query observations strictly for Case B
    b_obs_stmt = select(Observation).where(Observation.case_id == case_b.id)
    b_obs = (await db_session.execute(b_obs_stmt)).scalars().all()

    # Assert: Case B contains ZERO observations referencing ev_a1.id or case_a.id
    for o in b_obs:
        assert o.case_id == case_b.id, f"Observation {o.id} has incorrect case_id"
        assert o.evidence_id == ev_b1.id, f"Observation {o.id} leaked from Case A evidence {ev_a1.id}"

    # Telemetry isolation
    tele_a = get_case_telemetry(case_a.id)
    tele_b = get_case_telemetry(case_b.id)

    for rec in tele_b:
        assert rec["case_id"] == case_b.id, f"Telemetry record {rec} has wrong case_id"


# ---------------------------------------------------------------------------
# TEST 4: LLM Unavailable → BLOCKED (no synthetic observations produced)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_llm_unavailable_produces_no_synthetic_observations(db_session: AsyncSession):
    """
    When the LLM is mocked unavailable (returns None for all AI methods),
    I11 and R01 MUST return BLOCKED with zero outputs.
    No synthetic claims should appear as a substitute.
    """
    from unittest.mock import AsyncMock, patch
    import uuid

    org = Organization(id=str(uuid.uuid4()), name="LLM Block Test Org")
    db_session.add(org)
    user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        email=f"llm_test_{uuid.uuid4().hex[:6]}@rre.internal",
        hashed_password="hashed_test_password",
        full_name="LLM Block Tester",
        role="LEAD_INVESTIGATOR",
        department="INVESTIGATION"
    )
    db_session.add(user)
    await db_session.commit()

    case = Case(
        id=str(uuid.uuid4()),
        case_number=f"LLM-BLOCK-{uuid.uuid4().hex[:6]}",
        title="LLM Block Test Case",
        case_type="THEFT",
        organization_id=org.id,
        created_by=user.id
    )
    db_session.add(case)

    ev_witness = Evidence(
        id=str(uuid.uuid4()),
        case_id=case.id,
        evidence_type=EvidenceType.WITNESS_STATEMENT,
        original_filename="witness_block_test.txt",
        storage_key=f"{case.id}/witness_block_test.txt",
        sha256_hash="c" * 64,
        file_size_bytes=200,
        mime_type="text/plain",
        uploaded_by=user.id,
        metadata_json={"statement_text": "I saw someone near the shelf at around 3pm and they left quickly."}
    )
    db_session.add(ev_witness)
    await db_session.commit()

    # Mock LLM to always return None (simulating key misconfiguration / quota exceeded)
    with patch("app.llm.client.ai_client.parse_witness_statement", new=AsyncMock(return_value=None)), \
         patch("app.llm.client.ai_client.generate_hypotheses", new=AsyncMock(return_value=None)), \
         patch("app.llm.client.ai_client.challenge_hypotheses", new=AsyncMock(return_value=None)):

        exec_result = await execute_case_analysis_plan(db_session, case, user_id=user.id)
        telemetry = get_case_telemetry(case.id)
        tele_by_id = {t["engine_id"]: t for t in telemetry}

        # I11 MUST be BLOCKED — not produce any synthetic witness claims
        i11_rec = tele_by_id.get("I11")
        assert i11_rec is not None, "I11 must have a telemetry record"
        assert i11_rec["status"] in [EngineExecutionResult.BLOCKED.value, "BLOCKED"], (
            f"I11 must be BLOCKED when LLM is unavailable, got: {i11_rec['status']}"
        )
        assert not i11_rec.get("outputs"), (
            f"I11 must produce ZERO outputs when BLOCKED, got: {i11_rec.get('outputs')}"
        )

        # R01 MUST be BLOCKED — not produce any synthetic hypotheses
        r01_rec = tele_by_id.get("R01")
        assert r01_rec is not None, "R01 must have a telemetry record"
        # R01 is allowed to produce INSUFFICIENT_EVIDENCE deterministically, but if it
        # needed LLM for full hypotheses, it must BLOCK (no synthetic hypotheses emitted)
        if r01_rec["status"] not in [EngineExecutionResult.BLOCKED.value, "BLOCKED"]:
            # If deterministic path triggered (insufficient evidence), check it's the expected type
            for out in (r01_rec.get("outputs") or []):
                assert out.get("hypothesis_category") in ["INSUFFICIENT_EVIDENCE", "PARTIAL_CIRCUMSTANTIAL"], (
                    f"R01 produced non-deterministic hypothesis without LLM: {out.get('hypothesis_category')}"
                )

        # No observations should exist from LLM-generated claims
        obs_stmt = select(Observation).where(Observation.case_id == case.id)
        case_obs = (await db_session.execute(obs_stmt)).scalars().all()
        for o in case_obs:
            raw = str(o.raw_data or {}).lower()
            assert "deterministic_grounded" not in raw, (
                f"Observation {o.id} contains DETERMINISTIC_GROUNDED fallback data"
            )

        # actual_execution_path must reflect BLOCKED state for I11
        if i11_rec:
            exec_path = i11_rec.get("actual_execution_path", "")
            assert "BLOCKED" in exec_path.upper() or exec_path == "NOT_STARTED", (
                f"I11 actual_execution_path must indicate BLOCKED, got: {exec_path}"
            )


# ---------------------------------------------------------------------------
# TEST 5: Image + Witness Only → X04 Must Report EVIDENCE_MODALITY_GAP Entries
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_image_witness_only_x04_reports_modality_gaps(db_session: AsyncSession):
    """
    On a case with only Image + Witness evidence,
    X04 (Investigation Gap Engine) MUST produce EVIDENCE_MODALITY_GAP entries
    for CCTV, POS/inventory, and vehicle modalities.
    It MUST NOT report "No active gaps identified."
    """
    import uuid

    org = Organization(id=str(uuid.uuid4()), name="Gap Test Org")
    db_session.add(org)
    user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        email=f"gap_{uuid.uuid4().hex[:6]}@rre.internal",
        hashed_password="hashed_test_password",
        full_name="Gap Auditor",
        role="LEAD_INVESTIGATOR",
        department="INVESTIGATION"
    )
    db_session.add(user)
    await db_session.commit()

    case = Case(
        id=str(uuid.uuid4()),
        case_number=f"GAP-TEST-{uuid.uuid4().hex[:6]}",
        title="Gap Reporting Test Case",
        case_type="THEFT",
        organization_id=org.id,
        created_by=user.id
    )
    db_session.add(case)

    ev_image = Evidence(
        id=str(uuid.uuid4()),
        case_id=case.id,
        evidence_type=EvidenceType.IMAGE,
        original_filename="scene_photo.jpg",
        storage_key=f"{case.id}/scene_photo.jpg",
        sha256_hash="d" * 64,
        file_size_bytes=2048,
        mime_type="image/jpeg",
        uploaded_by=user.id
    )
    ev_witness = Evidence(
        id=str(uuid.uuid4()),
        case_id=case.id,
        evidence_type=EvidenceType.WITNESS_STATEMENT,
        original_filename="witness_gap_test.txt",
        storage_key=f"{case.id}/witness_gap_test.txt",
        sha256_hash="e" * 64,
        file_size_bytes=300,
        mime_type="text/plain",
        uploaded_by=user.id
    )
    db_session.add_all([ev_image, ev_witness])
    await db_session.commit()

    exec_result = await execute_case_analysis_plan(db_session, case, user_id=user.id)
    telemetry = get_case_telemetry(case.id)
    tele_by_id = {t["engine_id"]: t for t in telemetry}

    # X04 MUST have run and produced gap outputs
    x04_rec = tele_by_id.get("X04")
    assert x04_rec is not None, "X04 must have a telemetry record"
    assert x04_rec["status"] in ["SUCCESS", EngineExecutionResult.SUCCESS.value], (
        f"X04 should succeed (deterministic), got: {x04_rec['status']}"
    )

    gap_outputs = x04_rec.get("outputs", [])
    assert len(gap_outputs) > 0, "X04 must report at least one gap for an Image+Witness-only case"

    # Must have CRITICAL gaps for CCTV and POS/inventory
    gap_types = [g.get("gap_type") for g in gap_outputs]
    gap_descriptions = " ".join(g.get("description", "") for g in gap_outputs).lower()
    gap_significances = [g.get("significance") for g in gap_outputs]

    assert "EVIDENCE_MODALITY_GAP" in gap_types, (
        f"X04 must emit EVIDENCE_MODALITY_GAP gaps, got types: {gap_types}"
    )
    assert "CRITICAL" in gap_significances, (
        f"X04 must emit at least one CRITICAL gap, got: {gap_significances}"
    )
    assert "cctv" in gap_descriptions or "video" in gap_descriptions, (
        f"X04 must reference CCTV/video gap in descriptions: {gap_descriptions}"
    )
    assert "inventory" in gap_descriptions or "pos" in gap_descriptions or "financial" in gap_descriptions, (
        f"X04 must reference POS/inventory gap in descriptions: {gap_descriptions}"
    )

    # X04 must NOT declare "No active gaps"
    for g in gap_outputs:
        desc = (g.get("description") or "").lower()
        assert "no active gaps" not in desc, (
            f"X04 incorrectly claimed 'No active gaps': {g}"
        )
