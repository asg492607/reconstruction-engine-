import pytest
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from app.department_engines.framework.registry import engine_registry
from app.department_engines.framework.base import (
    EngineContext,
    EngineExecutionRecord,
    EngineExecutionResult,
    ExecutionMode,
    AnalysisRunContext
)
from app.reconstruction.final_verification_engine import (
    FinalVerificationEngine,
    FinalVerificationDetermination
)


@pytest.mark.asyncio
async def test_i11_modality_scoping_rejection():
    """
    Test I11 (Witness Intelligence Engine):
    - Must ONLY accept WITNESS_STATEMENT or AUDIO inputs.
    - Must NOT execute against generic documents or CSV alarm logs.
    """
    i11 = engine_registry.get("I11")
    assert i11 is not None

    class MockEvidence:
        def __init__(self, id, evidence_type, filename):
            self.id = id
            self.evidence_type = evidence_type
            self.original_filename = filename

    ctx = EngineContext(
        case_id="case_modality_test",
        analysis_version=1,
        analysis_run_id="RUN_MOD_001",
        run_context=AnalysisRunContext(
            case_id="case_modality_test",
            analysis_version=1,
            analysis_run_id="RUN_MOD_001"
        )
    )

    # 1. Test CSV alarm log rejection
    csv_ev = MockEvidence("ev_csv", "TRANSACTION_RECORD", "perimeter_alarm_log.csv")
    rec_csv = await i11.execute("case_modality_test", csv_ev, ctx)
    assert rec_csv.status == EngineExecutionResult.BLOCKED
    assert rec_csv.actual_execution_path == "BLOCKED_UNAVAILABLE_MODALITY"
    assert "WITNESS_STATEMENT or AUDIO" in (rec_csv.failure_reason or "")

    # 2. Test generic document rejection
    doc_ev = MockEvidence("ev_doc", "DOCUMENT", "inventory_summary.pdf")
    rec_doc = await i11.execute("case_modality_test", doc_ev, ctx)
    assert rec_doc.status == EngineExecutionResult.BLOCKED
    assert rec_doc.actual_execution_path == "BLOCKED_UNAVAILABLE_MODALITY"

    # 3. Test accepted witness statement (passes modality check, proceeds to LLM check)
    wit_ev = MockEvidence("ev_wit", "WITNESS_STATEMENT", "statement_clerk.txt")
    rec_wit = await i11.execute("case_modality_test", wit_ev, ctx)
    # Status can be BLOCKED_LLM_UNAVAILABLE or SUCCESS depending on API key, but NOT BLOCKED_UNAVAILABLE_MODALITY
    assert rec_wit.actual_execution_path != "BLOCKED_UNAVAILABLE_MODALITY"


@pytest.mark.asyncio
async def test_x05_canonical_run_state_consumption():
    """
    Test X05 (Conflict & Discrepancy Engine):
    - Must consume actual persisted execution states from active case_id + analysis_version + analysis_run_id.
    - Must not reconstruct availability independently.
    """
    x05 = engine_registry.get("X05")
    assert x05 is not None

    case_id = f"case_x05_{uuid.uuid4().hex[:6]}"
    version = 3
    run_id = "RUN_CANONICAL_99"

    ctx = EngineContext(
        case_id=case_id,
        analysis_version=version,
        analysis_run_id=run_id,
        run_context=AnalysisRunContext(
            case_id=case_id,
            analysis_version=version,
            analysis_run_id=run_id
        )
    )

    # Populate explicit prior results
    ctx.prior_results["I01"] = EngineExecutionRecord(
        case_id=case_id,
        analysis_version=version,
        analysis_run_id=run_id,
        engine_id="I01",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC,
        status=EngineExecutionResult.SUCCESS,
        outputs=[{"cctv_active": True}]
    )
    ctx.prior_results["I11"] = EngineExecutionRecord(
        case_id=case_id,
        analysis_version=version,
        analysis_run_id=run_id,
        engine_id="I11",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.HYBRID,
        status=EngineExecutionResult.BLOCKED,
        actual_execution_path="BLOCKED_UNAVAILABLE_MODALITY",
        failure_reason="No witness statement attached"
    )
    ctx.prior_results["X02"] = EngineExecutionRecord(
        case_id=case_id,
        analysis_version=version,
        analysis_run_id=run_id,
        engine_id="X02",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC,
        status=EngineExecutionResult.SUCCESS,
        outputs=[
            {"event_id": "EV_01", "event_type": "ZONE_ENTRY", "timestamp": "2026-09-07T10:00:00Z", "source_id": "I01"},
            {"event_id": "EV_02", "event_type": "POS_TRANSACTION", "timestamp": "2026-09-07T10:05:00Z", "source_id": "FI04"}
        ]
    )

    rec_x05 = await x05.execute(case_id, None, ctx)
    assert rec_x05.status == EngineExecutionResult.SUCCESS

    # Verify canonical_run_state in provenance
    assert rec_x05.provenance, "Provenance must be populated with canonical_run_state"
    canonical_state = rec_x05.provenance[0].get("canonical_run_state")
    assert canonical_state is not None
    assert canonical_state["case_id"] == case_id
    assert canonical_state["analysis_version"] == version
    assert canonical_state["analysis_run_id"] == run_id
    assert canonical_state["total_prior_engines"] == 3

    # Check exact engine states
    assert canonical_state["engine_states"]["I01"]["status"] == "SUCCESS"
    assert canonical_state["engine_states"]["I11"]["status"] == "BLOCKED"
    assert canonical_state["engine_states"]["X02"]["status"] == "SUCCESS"

    # Verify grounding sources cite active run and canonical state
    grounding_str = " ".join(rec_x05.grounding_sources)
    assert run_id in grounding_str
    assert f"v{version}" in grounding_str


@pytest.mark.asyncio
async def test_x02_x03_x06_count_consistency():
    """
    Test exact count consistency across X02, X03, and X06:
    - X06.correlated_event_count == X03.correlated_event_count (0 for context mismatch / limited)
    - X06.source_event_count == X02 source event count
    """
    x02 = engine_registry.get("X02")
    x03 = engine_registry.get("X03")
    x06 = engine_registry.get("X06")

    case_id = f"case_count_{uuid.uuid4().hex[:6]}"
    version = 1
    run_id = "RUN_COUNT_TEST"

    ctx = EngineContext(
        case_id=case_id,
        analysis_version=version,
        analysis_run_id=run_id,
        run_context=AnalysisRunContext(
            case_id=case_id,
            analysis_version=version,
            analysis_run_id=run_id,
            evidence_manifest=[
                {"evidence_id": "ev_img", "filename": "Screenshot 2026-09-07 101902.png", "evidence_type": "IMAGE"},
                {"evidence_id": "ev_vid", "filename": "u_can_generate_images_and_s.mp4", "evidence_type": "VIDEO"},
                {"evidence_id": "ev_csv", "filename": "ledger.csv", "evidence_type": "TRANSACTION_RECORD"}
            ]
        )
    )

    # Provide prior I12 and F01 results for X02
    ctx.prior_results["I12"] = EngineExecutionRecord(
        case_id=case_id,
        analysis_version=version,
        analysis_run_id=run_id,
        engine_id="I12",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC,
        status=EngineExecutionResult.SUCCESS,
        outputs=[{
            "event_id": "EV_VID_01",
            "event_name": "Facility loading dock activity",
            "location": "Loading Dock",
            "timestamp": "2026-09-07T10:02:15Z",
            "event_type": "ZONE_ENTRY",
            "source_id": "ev_vid"
        }]
    )
    ctx.prior_results["F01"] = EngineExecutionRecord(
        case_id=case_id,
        analysis_version=version,
        analysis_run_id=run_id,
        engine_id="F01",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC,
        status=EngineExecutionResult.SUCCESS,
        outputs=[{
            "image_id": "IMG_01",
            "original_capture_time": "2026-09-07T10:19:02Z",
            "camera_model": "Forensic Macro Lens",
            "source_id": "ev_img"
        }]
    )

    # Execute X02
    rec_x02 = await x02.execute(case_id, None, ctx)
    ctx.prior_results["X02"] = rec_x02
    source_count = len([e for e in rec_x02.outputs if e.get("source_modality") != "SYSTEM_RECORD"])
    assert source_count >= 2

    # Execute X03 (disparate exhibits -> context mismatch -> correlated_event_count == 0)
    rec_x03 = await x03.execute(case_id, None, ctx)
    ctx.prior_results["X03"] = rec_x03
    assert rec_x03.outputs[0].get("correlated_event_count") == 0

    # Execute X06
    rec_x06 = await x06.execute(case_id, None, ctx)
    ctx.prior_results["X06"] = rec_x06
    x06_out = rec_x06.outputs[0]

    # Verify exact equality
    assert x06_out["correlated_event_count"] == rec_x03.outputs[0]["correlated_event_count"] == 0
    assert x06_out["source_event_count"] == source_count

    # Run FinalVerificationEngine to ensure Check 15 passes
    fve = FinalVerificationEngine()
    res = fve.verify(
        engine_outputs=ctx.prior_results,
        valid_evidence_ids={"ev_img", "ev_vid", "ev_csv"},
        case_id=case_id,
        analysis_version=version
    )
    assert "CHECK_15_COUNT_CONSISTENCY" in res.checks_passed
    assert not any(i.check_id == "COUNT_CONSISTENCY_MISMATCH" for i in res.issues)


@pytest.mark.asyncio
async def test_timeline_event_schema_and_artifact_exclusion():
    """
    Test X02 timeline event schema:
    - Events contain only semantic investigative events: event_type, timestamp, source_id, observation_refs, provenance.
    - No debug / engine-record artifacts ('record from', 'I1 record', 'F0 record').
    """
    x02 = engine_registry.get("X02")
    case_id = f"case_tl_{uuid.uuid4().hex[:6]}"

    ctx = EngineContext(
        case_id=case_id,
        analysis_version=1,
        analysis_run_id="RUN_TL_TEST"
    )

    ctx.prior_results["I12"] = EngineExecutionRecord(
        case_id=case_id,
        analysis_version=1,
        analysis_run_id="RUN_TL_TEST",
        engine_id="I12",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC,
        status=EngineExecutionResult.SUCCESS,
        outputs=[{
            "event_id": "EV_I12_01",
            "event_name": "Optical motion detected",
            "location": "North Hall",
            "timestamp": "2026-09-07T08:30:00Z",
            "event_type": "ZONE_ENTRY",
            "source_id": "ev_cam1"
        }]
    )

    rec_x02 = await x02.execute(case_id, None, ctx)
    assert rec_x02.status == EngineExecutionResult.SUCCESS
    assert len(rec_x02.outputs) >= 1

    for ev in rec_x02.outputs:
        # Schema field checks
        assert "event_type" in ev
        assert "timestamp" in ev
        assert "source_id" in ev
        assert "observation_refs" in ev
        assert "provenance" in ev

        desc = (ev.get("description") or ev.get("label") or "").lower()
        # Verify no debug artifacts
        assert "record from" not in desc
        assert "debug" not in desc

        # Verify event_type is not an internal engine abbreviation
        ev_type = str(ev.get("event_type", ""))
        assert not any(ev_type.upper().startswith(p) for p in ("I0", "I1", "F0", "X0", "FI0", "FI1", "R0"))

    # Verify FVE Check 16 passes
    fve = FinalVerificationEngine()
    res = fve.verify(
        engine_outputs={
            "X02": rec_x02,
            "X03": EngineExecutionRecord(
                case_id=case_id, analysis_version=1, engine_id="X03", engine_version="1.0.0",
                execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.SUCCESS,
                outputs=[{"correlated_event_count": 0, "correlation_type": "LIMITED_NO_DEFENSIBLE_LINK"}]
            ),
            "X06": EngineExecutionRecord(
                case_id=case_id, analysis_version=1, engine_id="X06", engine_version="1.0.0",
                execution_mode=ExecutionMode.HYBRID, status=EngineExecutionResult.SUCCESS,
                outputs=[{"correlated_event_count": 0, "source_event_count": len(rec_x02.outputs)}]
            )
        },
        valid_evidence_ids={"ev_cam1"},
        case_id=case_id,
        analysis_version=1
    )
    assert "CHECK_16_TIMELINE_EVENT_SCHEMA" in res.checks_passed
    assert not any(i.check_id == "TIMELINE_SCHEMA_VIOLATION" for i in res.issues)


def test_fve_hard_invariants_flag_violations():
    """
    Test that FinalVerificationEngine raises hard integrity violations when invariants are broken:
    1. INPUT_MODALITY_SCOPE_VIOLATION (I11 succeeded on CSV evidence)
    2. CANONICAL_RUN_STATE_MISMATCH (X05 state diverges from actual execution)
    3. COUNT_CONSISTENCY_MISMATCH (X06 count differs from X03)
    4. TIMELINE_SCHEMA_VIOLATION (Debug artifact in timeline)
    """
    fve = FinalVerificationEngine()
    case_id = "case_invariants_violation"

    # 1. Test I11 modality violation
    invalid_i11_rec = EngineExecutionRecord(
        case_id=case_id, analysis_version=1, engine_id="I11", engine_version="1.0.0",
        execution_mode=ExecutionMode.HYBRID, status=EngineExecutionResult.SUCCESS,
        grounding_sources=["ledger.csv (TRANSACTION_RECORD)"],
        outputs=[{"actor_described": "Subject in hoodie"}]
    )
    res_i11 = fve.verify(
        engine_outputs={"I11": invalid_i11_rec},
        valid_evidence_ids={"ev_csv"},
        case_id=case_id,
        evidence_manifest=[{"evidence_id": "ev_csv", "evidence_type": "TRANSACTION_RECORD", "original_filename": "ledger.csv"}]
    )
    assert res_i11.determination == FinalVerificationDetermination.HARD_INTEGRITY_VIOLATION
    assert any(i.check_id == "INPUT_MODALITY_SCOPE_VIOLATION" for i in res_i11.issues)

    # 2. Test X05 canonical run state mismatch
    invalid_x05_rec = EngineExecutionRecord(
        case_id=case_id, analysis_version=1, engine_id="X05", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.SUCCESS,
        provenance=[{"canonical_run_state": {
            "case_id": case_id,
            "analysis_version": 1,
            "engine_states": {
                "I01": {"status": "SUCCESS"}  # Claims I01 was SUCCESS
            }
        }}],
        outputs=[]
    )
    # Actual I01 was BLOCKED:
    actual_i01_rec = EngineExecutionRecord(
        case_id=case_id, analysis_version=1, engine_id="I01", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.BLOCKED
    )
    res_x05 = fve.verify(
        engine_outputs={"I01": actual_i01_rec, "X05": invalid_x05_rec},
        valid_evidence_ids={"ev_01"},
        case_id=case_id
    )
    assert res_x05.determination == FinalVerificationDetermination.HARD_INTEGRITY_VIOLATION
    assert any(i.check_id == "CANONICAL_RUN_STATE_MISMATCH" for i in res_x05.issues)

    # 3. Test X06 vs X03 count mismatch
    mismatched_x03 = EngineExecutionRecord(
        case_id=case_id, analysis_version=1, engine_id="X03", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.SUCCESS,
        outputs=[{"correlated_event_count": 0, "correlation_type": "LIMITED_NO_DEFENSIBLE_LINK"}]
    )
    mismatched_x06 = EngineExecutionRecord(
        case_id=case_id, analysis_version=1, engine_id="X06", engine_version="1.0.0",
        execution_mode=ExecutionMode.HYBRID, status=EngineExecutionResult.SUCCESS,
        outputs=[{"correlated_event_count": 4, "source_event_count": 2}]
    )
    res_count = fve.verify(
        engine_outputs={"X03": mismatched_x03, "X06": mismatched_x06},
        valid_evidence_ids={"ev_01"},
        case_id=case_id
    )
    assert res_count.determination == FinalVerificationDetermination.HARD_INTEGRITY_VIOLATION
    assert any(i.check_id == "COUNT_CONSISTENCY_MISMATCH" for i in res_count.issues)

    # 4. Test timeline debug artifact
    polluted_x02 = EngineExecutionRecord(
        case_id=case_id, analysis_version=1, engine_id="X02", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.SUCCESS,
        outputs=[{
            "event_id": "EV_01",
            "event_type": "I1",
            "timestamp": "2026-09-07T10:00:00Z",
            "source_id": "0e74cde0",
            "description": "I1 record from 0e74cde0",
            "observation_refs": []
        }]
    )
    res_tl = fve.verify(
        engine_outputs={"X02": polluted_x02},
        valid_evidence_ids={"0e74cde0"},
        case_id=case_id
    )
    assert res_tl.determination == FinalVerificationDetermination.HARD_INTEGRITY_VIOLATION
    assert any(i.check_id == "TIMELINE_SCHEMA_VIOLATION" for i in res_tl.issues)
