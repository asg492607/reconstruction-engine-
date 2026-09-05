import pytest
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from app.department_engines.framework.registry import engine_registry
from app.department_engines.framework.validator import output_validator
from app.department_engines.framework.base import (
    EngineContext,
    EngineExecutionRecord,
    EngineExecutionResult,
    ExecutionMode
)


class MockEvidence:
    def __init__(self, id: str, evidence_type: str, file_path: str = "test.dat", metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.evidence_type = evidence_type
        self.original_filename = file_path
        self.file_path = file_path
        self.file_size_bytes = 1048576
        self.mime_type = "image/jpeg" if evidence_type == "IMAGE" else ("video/mp4" if evidence_type == "CCTV" else "text/plain")
        self.sha256_hash = f"hash_{id}"
        self.created_at = datetime.now(timezone.utc)
        self.metadata_json = metadata or {}


# ===========================================================================
# 1. Regression Test: None confidence
# ===========================================================================
def test_regression_none_confidence():
    """Ensure record.confidence = None does NOT raise TypeError: '<' not supported between instances of 'NoneType' and 'float'."""
    x06_engine = engine_registry.get("X06")
    assert x06_engine is not None

    record = EngineExecutionRecord(
        case_id="case_none_conf",
        engine_id="X06",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.HYBRID,
        status=EngineExecutionResult.SUCCESS,
        confidence=None,
        outputs=[{
            "sufficiency_rating": "INSUFFICIENT_FOR_RECONSTRUCTION",
            "proceed_to_reconstruction": False,
            "summary": "Evidence insufficient for defensible reconstruction."
        }]
    )

    # Validate output through OutputValidator: must not raise TypeError on confidence comparisons
    validated = output_validator.validate(record, x06_engine.definition)
    assert validated.status == EngineExecutionResult.SUCCESS
    assert validated.confidence is None
    assert validated.review_status == "LEAD_REVIEW_REQUIRED"


# ===========================================================================
# 2. Regression Test: Missing timestamp
# ===========================================================================
@pytest.mark.asyncio
async def test_regression_missing_timestamp():
    """Ensure exhibits or events with missing timestamps evaluate safely in X02 and X06."""
    x02 = engine_registry.get("X02")
    x06 = engine_registry.get("X06")
    assert x02 is not None and x06 is not None

    # Exhibits without timestamp
    ctx = EngineContext(case_id="case_no_timestamp")
    # F01 ran but original_capture_time is None
    f01_rec = EngineExecutionRecord(
        case_id="case_no_timestamp",
        engine_id="F01",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC,
        status=EngineExecutionResult.SUCCESS,
        outputs=[{
            "original_capture_time": None,
            "camera_model": "Forensic Camera"
        }]
    )
    ctx.prior_results["F01"] = f01_rec

    rec_x02 = await x02.execute(case_id="case_no_timestamp", evidence=None, context=ctx)
    # X02 should recognize no valid timestamps found and return NO_USABLE_OUTPUT
    assert rec_x02.status == EngineExecutionResult.NO_USABLE_OUTPUT
    assert rec_x02.confidence is None
    ctx.prior_results["X02"] = rec_x02

    # Now run X06
    rec_x06 = await x06.execute(case_id="case_no_timestamp", evidence=None, context=ctx)
    assert rec_x06.status == EngineExecutionResult.SUCCESS
    assert rec_x06.confidence is None
    out = rec_x06.outputs[0]
    assert out["sufficiency_rating"] == "INSUFFICIENT_FOR_RECONSTRUCTION"
    assert out["proceed_to_reconstruction"] is False
    assert out["evaluation_criteria"]["temporal_anchor_established"] is False


# ===========================================================================
# 3. Regression Test: Missing spatial measurement
# ===========================================================================
@pytest.mark.asyncio
async def test_regression_missing_spatial_measurement():
    """Ensure missing spatial distance in R02 returns NOT_ASSESSABLE without TypeError."""
    r02 = engine_registry.get("R02")
    assert r02 is not None

    ctx = EngineContext(case_id="case_no_spatial")
    # Provide an R01 output so R02 can proceed to feasibility evaluation
    r01_rec = EngineExecutionRecord(
        case_id="case_no_spatial",
        engine_id="R01",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC,
        status=EngineExecutionResult.PARTIAL,
        outputs=[{"hypothesis_id": "HYP_01", "hypothesis_title": "Test Sequence"}]
    )
    ctx.prior_results["R01"] = r01_rec

    # I10 has output but unmonitored_distance_meters is None
    i10_rec = EngineExecutionRecord(
        case_id="case_no_spatial",
        engine_id="I10",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC,
        status=EngineExecutionResult.SUCCESS,
        outputs=[{"unmonitored_distance_meters": None}]
    )
    ctx.prior_results["I10"] = i10_rec

    rec_r02 = await r02.execute(case_id="case_no_spatial", evidence=None, context=ctx)
    assert rec_r02.status == EngineExecutionResult.SUCCESS
    checks = {c["check_name"]: c["status"] for c in rec_r02.outputs}
    assert checks["TRANSIT_VELOCITY_FEASIBILITY"] == "NOT_ASSESSABLE"


# ===========================================================================
# 4. Regression Test: Empty observation list
# ===========================================================================
@pytest.mark.asyncio
async def test_regression_empty_observation_list():
    """Ensure engines with empty observation outputs don't crash and return NO_USABLE_OUTPUT."""
    x01 = engine_registry.get("X01")
    assert x01 is not None

    ctx = EngineContext(case_id="case_empty_obs")
    rec_x01 = await x01.execute(case_id="case_empty_obs", evidence=None, context=ctx)
    assert rec_x01.status == EngineExecutionResult.NO_USABLE_OUTPUT
    assert rec_x01.confidence is None
    assert rec_x01.outputs == []


# ===========================================================================
# 5. Regression Test: Image-only case
# ===========================================================================
@pytest.mark.asyncio
async def test_regression_image_only_case():
    """Image-only exhibit: X06 succeeds with INSUFFICIENT_FOR_RECONSTRUCTION, downstream R01-R03 blocked."""
    x06 = engine_registry.get("X06")
    r01 = engine_registry.get("R01")
    r02 = engine_registry.get("R02")
    r03 = engine_registry.get("R03")

    ctx = EngineContext(case_id="case_image_only")
    ev = MockEvidence(id="ev_img_01", evidence_type="IMAGE", metadata={"camera_model": "Nikon D850"})

    # Prior engines: F01 and F02 succeeded, no video, no inventory
    ctx.prior_results["F01"] = EngineExecutionRecord(
        case_id="case_image_only", engine_id="F01", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.SUCCESS,
        outputs=[{"camera_model": "Nikon D850", "original_capture_time": None}]
    )
    ctx.prior_results["X02"] = EngineExecutionRecord(
        case_id="case_image_only", engine_id="X02", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.NO_USABLE_OUTPUT,
        confidence=None, outputs=[]
    )

    rec_x06 = await x06.execute(case_id="case_image_only", evidence=ev, context=ctx)
    assert rec_x06.status == EngineExecutionResult.SUCCESS
    assert rec_x06.confidence is None
    assert rec_x06.outputs[0]["sufficiency_rating"] == "INSUFFICIENT_FOR_RECONSTRUCTION"
    assert rec_x06.outputs[0]["proceed_to_reconstruction"] is False
    ctx.prior_results["X06"] = rec_x06

    # Downstream R01 must be BLOCKED
    rec_r01 = await r01.execute(case_id="case_image_only", evidence=ev, context=ctx)
    assert rec_r01.status == EngineExecutionResult.BLOCKED
    assert rec_r01.confidence is None
    ctx.prior_results["R01"] = rec_r01

    # Downstream R02 must be BLOCKED
    rec_r02 = await r02.execute(case_id="case_image_only", evidence=ev, context=ctx)
    assert rec_r02.status == EngineExecutionResult.BLOCKED
    assert rec_r02.confidence is None
    ctx.prior_results["R02"] = rec_r02

    # Downstream R03 must be BLOCKED
    rec_r03 = await r03.execute(case_id="case_image_only", evidence=ev, context=ctx)
    assert rec_r03.status == EngineExecutionResult.BLOCKED
    assert rec_r03.confidence is None


# ===========================================================================
# 6. Regression Test: Image + Witness case (Current two-exhibit test)
# ===========================================================================
@pytest.mark.asyncio
async def test_regression_image_plus_witness_case():
    """Image + Witness statement: no CCTV or inventory -> X06 is INSUFFICIENT, R01-R03 BLOCKED."""
    x06 = engine_registry.get("X06")
    r01 = engine_registry.get("R01")
    r02 = engine_registry.get("R02")
    r03 = engine_registry.get("R03")

    ctx = EngineContext(case_id="case_img_wit")
    ev_img = MockEvidence(id="ev_img_02", evidence_type="IMAGE")
    ev_wit = MockEvidence(id="ev_wit_01", evidence_type="WITNESS_STATEMENT")

    # Image engines ran, witness ran (or I11 blocked)
    ctx.prior_results["F01"] = EngineExecutionRecord(
        case_id="case_img_wit", engine_id="F01", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.SUCCESS,
        outputs=[{"camera_model": "Phone Camera"}]
    )
    ctx.prior_results["I11"] = EngineExecutionRecord(
        case_id="case_img_wit", engine_id="I11", engine_version="1.0.0",
        execution_mode=ExecutionMode.MODEL, status=EngineExecutionResult.BLOCKED,
        failure_reason="LLM provider unavailable", outputs=[]
    )
    ctx.prior_results["X02"] = EngineExecutionRecord(
        case_id="case_img_wit", engine_id="X02", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.NO_USABLE_OUTPUT,
        confidence=None, outputs=[]
    )

    rec_x06 = await x06.execute(case_id="case_img_wit", evidence=ev_img, context=ctx)
    assert rec_x06.status == EngineExecutionResult.SUCCESS
    assert rec_x06.confidence is None
    assert rec_x06.outputs[0]["sufficiency_rating"] == "INSUFFICIENT_FOR_RECONSTRUCTION"
    assert rec_x06.outputs[0]["proceed_to_reconstruction"] is False
    ctx.prior_results["X06"] = rec_x06

    # Downstream R01 must be BLOCKED
    rec_r01 = await r01.execute(case_id="case_img_wit", evidence=ev_img, context=ctx)
    assert rec_r01.status == EngineExecutionResult.BLOCKED
    assert rec_r01.confidence is None
    ctx.prior_results["R01"] = rec_r01

    # Downstream R02 must be BLOCKED
    rec_r02 = await r02.execute(case_id="case_img_wit", evidence=ev_img, context=ctx)
    assert rec_r02.status == EngineExecutionResult.BLOCKED
    assert rec_r02.confidence is None
    ctx.prior_results["R02"] = rec_r02

    # Downstream R03 must be BLOCKED
    rec_r03 = await r03.execute(case_id="case_img_wit", evidence=ev_img, context=ctx)
    assert rec_r03.status == EngineExecutionResult.BLOCKED
    assert rec_r03.confidence is None


# ===========================================================================
# 7. Regression Test: CCTV-only case
# ===========================================================================
@pytest.mark.asyncio
async def test_regression_cctv_only_case():
    """CCTV-only: has video events, but missing inventory -> X04 detects critical gap, X06 yields MARGINAL_PROBATIVE_VALUE."""
    x04 = engine_registry.get("X04")
    x06 = engine_registry.get("X06")
    assert x04 is not None and x06 is not None

    ctx = EngineContext(case_id="case_cctv_only")
    ev_cctv = MockEvidence(id="ev_cctv_01", evidence_type="CCTV")

    # Video engine I01 & I03 succeeded
    ctx.prior_results["I01"] = EngineExecutionRecord(
        case_id="case_cctv_only", engine_id="I01", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.SUCCESS,
        outputs=[{"frame_count": 300, "fps": 30.0}]
    )
    ctx.prior_results["I03"] = EngineExecutionRecord(
        case_id="case_cctv_only", engine_id="I03", engine_version="1.0.0",
        execution_mode=ExecutionMode.MODEL, status=EngineExecutionResult.SUCCESS,
        outputs=[{"class_name": "person", "track_id": "TRK_01"}]
    )
    # X02 has video events
    ctx.prior_results["X02"] = EngineExecutionRecord(
        case_id="case_cctv_only", engine_id="X02", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.PARTIAL,
        outputs=[{"event_id": "TL_CCTV_1", "timestamp": "2026-09-05T12:00:00Z", "source_modality": "CCTV_VIDEO"}]
    )

    # Run X04 to detect missing inventory / financial modality gap
    rec_x04 = await x04.execute(case_id="case_cctv_only", evidence=ev_cctv, context=ctx)
    assert rec_x04.status == EngineExecutionResult.SUCCESS
    ctx.prior_results["X04"] = rec_x04
    critical_gaps = [g for g in rec_x04.outputs if g.get("significance") == "CRITICAL"]
    assert len(critical_gaps) > 0  # Inventory gap detected

    # Now run X06
    rec_x06 = await x06.execute(case_id="case_cctv_only", evidence=ev_cctv, context=ctx)
    assert rec_x06.status == EngineExecutionResult.SUCCESS
    assert rec_x06.outputs[0]["sufficiency_rating"] == "MARGINAL_PROBATIVE_VALUE"
    assert rec_x06.outputs[0]["proceed_to_reconstruction"] is True
    assert rec_x06.outputs[0]["evaluation_criteria"]["asset_delta_proven"] is False


# ===========================================================================
# 8. Regression Test: Complete Multi-Modal case
# ===========================================================================
@pytest.mark.asyncio
async def test_regression_complete_multimodal_case():
    """Complete multi-modal case: CCTV + Inventory + Forensic + Witness -> SUFFICIENT_FOR_RECONSTRUCTION."""
    x06 = engine_registry.get("X06")
    assert x06 is not None

    ctx = EngineContext(case_id="case_multimodal")
    ev_cctv = MockEvidence(id="ev_cctv_01", evidence_type="CCTV")

    # Video
    ctx.prior_results["I01"] = EngineExecutionRecord(
        case_id="case_multimodal", engine_id="I01", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.SUCCESS,
        outputs=[{"frame_count": 500}]
    )
    ctx.prior_results["I03"] = EngineExecutionRecord(
        case_id="case_multimodal", engine_id="I03", engine_version="1.0.0",
        execution_mode=ExecutionMode.MODEL, status=EngineExecutionResult.SUCCESS,
        outputs=[{"class_name": "person", "track_id": "TRK_01"}]
    )
    # Inventory
    ctx.prior_results["FI01"] = EngineExecutionRecord(
        case_id="case_multimodal", engine_id="FI01", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.SUCCESS,
        outputs=[{"sku": "SKU-990", "product_name": "Pro Camera"}]
    )
    ctx.prior_results["FI02"] = EngineExecutionRecord(
        case_id="case_multimodal", engine_id="FI02", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.SUCCESS,
        outputs=[{"total_missing_units": 1, "total_shrinkage_usd": 1200.0}]
    )
    # Witness
    ctx.prior_results["I11"] = EngineExecutionRecord(
        case_id="case_multimodal", engine_id="I11", engine_version="1.0.0",
        execution_mode=ExecutionMode.MODEL, status=EngineExecutionResult.SUCCESS,
        outputs=[{"actor_described": "tall male in dark jacket", "action_observed": "walking near shelf"}]
    )
    # Synchronized timeline events in X02
    ctx.prior_results["X02"] = EngineExecutionRecord(
        case_id="case_multimodal", engine_id="X02", engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC, status=EngineExecutionResult.SUCCESS,
        outputs=[
            {"event_id": "TL_CCTV_1", "timestamp": "2026-09-05T12:00:00Z", "source_modality": "CCTV_VIDEO"},
            {"event_id": "TL_POS_1", "timestamp": "2026-09-05T12:05:00Z", "source_modality": "POS_TRANSACTION"}
        ]
    )

    rec_x06 = await x06.execute(case_id="case_multimodal", evidence=ev_cctv, context=ctx)
    assert rec_x06.status == EngineExecutionResult.SUCCESS
    assert rec_x06.confidence == 0.90
    assert rec_x06.outputs[0]["sufficiency_rating"] == "SUFFICIENT_FOR_RECONSTRUCTION"
    assert rec_x06.outputs[0]["proceed_to_reconstruction"] is True


# ===========================================================================
# 9. Structured Failure Code: SUFFICIENCY_ASSESSMENT_UNAVAILABLE
# ===========================================================================
@pytest.mark.asyncio
async def test_regression_x06_unassessable_inputs_returns_failed():
    """When required inputs for sufficiency decision genuinely cannot be evaluated, return FAILED with structured code."""
    x06 = engine_registry.get("X06")
    assert x06 is not None

    # Context with prior_results missing/corrupted
    rec_failed = await x06.execute(case_id="case_corrupted", evidence=None, context=None)
    assert rec_failed.status == EngineExecutionResult.FAILED
    assert rec_failed.confidence is None
    assert "ERR_INPUTS_UNASSESSABLE" in rec_failed.failure_reason
    assert rec_failed.outputs[0]["sufficiency_rating"] == "SUFFICIENCY_ASSESSMENT_UNAVAILABLE"
    assert rec_failed.outputs[0]["failure_code"] == "ERR_INPUTS_UNASSESSABLE"
    assert rec_failed.outputs[0]["proceed_to_reconstruction"] is False
