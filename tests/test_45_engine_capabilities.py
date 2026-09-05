import pytest
import asyncio
from datetime import datetime, timezone, timedelta

from app.department_engines.framework.registry import engine_registry
from app.department_engines.framework.base import (
    EngineContext,
    EngineExecutionRecord,
    EngineExecutionResult
)
from app.department_engines.framework.validator import output_validator

class DummyEvidence:
    def __init__(self, id, ev_type, title="Evidence Exhibit", file_path="test.mp4", metadata=None, sha="sha256_valid", size=1048576):
        self.id = id
        self.evidence_type = ev_type
        self.title = title
        self.original_filename = file_path
        self.file_path = file_path
        self.file_size_bytes = size
        self.mime_type = "video/mp4" if ev_type == "CCTV" else "image/jpeg"
        self.sha256_hash = sha
        self.created_at = datetime.now(timezone.utc)
        self.metadata_json = metadata or {}


# ===========================================================================
# GROUP A: Evidence Foundation (E01–E07) Capability Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_e01_metadata_positive_and_missing():
    e01 = engine_registry.get("E01")
    ctx = EngineContext(case_id="case_cap_01")

    # Positive: valid exhibit
    ev_pos = DummyEvidence("ev_01", "CCTV", file_path="test_video.mp4")
    rec_pos = await e01.execute("case_cap_01", ev_pos, ctx)
    assert rec_pos.status == EngineExecutionResult.SUCCESS
    assert rec_pos.outputs[0]["mime_type"] == "video/mp4"

    # Degraded: None evidence
    rec_neg = await e01.execute("case_cap_01", None, ctx)
    assert rec_neg.status == EngineExecutionResult.NO_USABLE_OUTPUT


@pytest.mark.asyncio
async def test_e02_integrity_valid_and_mismatch():
    e02 = engine_registry.get("E02")
    ctx = EngineContext(case_id="case_cap_01")

    ev_pos = DummyEvidence("ev_02", "CCTV", sha="abc_hash_123")
    rec_pos = await e02.execute("case_cap_01", ev_pos, ctx)
    assert rec_pos.status == EngineExecutionResult.SUCCESS
    assert rec_pos.outputs[0]["integrity_status"] == "VERIFIED"


@pytest.mark.asyncio
async def test_e03_quality_high_vs_low_bitrate():
    e03 = engine_registry.get("E03")
    ctx = EngineContext(case_id="case_cap_01")

    # High bitrate
    ev_high = DummyEvidence("ev_high", "CCTV", size=50_000_000)
    rec_high = await e03.execute("case_cap_01", ev_high, ctx)
    assert rec_high.outputs[0]["quality_grade"] == "HIGH"

    # Low bitrate / degraded
    ev_low = DummyEvidence("ev_low", "CCTV", size=45_000)
    rec_low = await e03.execute("case_cap_01", ev_low, ctx)
    assert rec_low.outputs[0]["quality_grade"] == "LOW"


@pytest.mark.asyncio
async def test_e04_duplicate_detection():
    e04 = engine_registry.get("E04")
    ctx = EngineContext(case_id="case_cap_01")

    ev1 = DummyEvidence("ev_uniq", "IMAGE", sha="unique_sha_99")
    ev2 = DummyEvidence("ev_dup", "IMAGE", sha="unique_sha_99")

    rec1 = await e04.execute("case_cap_01", ev1, ctx)
    assert rec1.outputs[0]["is_duplicate"] is False

    rec2 = await e04.execute("case_cap_01", ev2, ctx)
    assert rec2.outputs[0]["is_duplicate"] is True


@pytest.mark.asyncio
async def test_e05_e06_e07_capabilities():
    e05 = engine_registry.get("E05")
    e06 = engine_registry.get("E06")
    e07 = engine_registry.get("E07")
    ctx = EngineContext(case_id="case_cap_01")

    ev_cctv = DummyEvidence("ev_cctv", "CCTV")
    rec_e05 = await e05.execute("case_cap_01", ev_cctv, ctx)
    assert rec_e05.outputs[0]["primary_department"] == "INVESTIGATION"

    rec_e06 = await e06.execute("case_cap_01", ev_cctv, ctx)
    assert rec_e06.outputs[0]["original_preserved"] is True

    rec_e07 = await e07.execute("case_cap_01", ev_cctv, ctx)
    assert rec_e07.outputs[0]["relationship_type"] == "CO_LOCATED_IN_CASE"


# ===========================================================================
# GROUP B: Investigation AI (I01–I12) Capability Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_i03_detection_and_i04_tracking():
    i03 = engine_registry.get("I03")
    i04 = engine_registry.get("I04")
    ctx = EngineContext(case_id="case_cap_02")

    # Clear detections
    ev_pos = DummyEvidence("ev_vid", "CCTV")
    rec_i03 = await i03.execute("case_cap_02", ev_pos, ctx)
    assert rec_i03.status == EngineExecutionResult.SUCCESS
    assert any(d["class_name"] == "person" for d in rec_i03.outputs)

    # Tracking associates into tracklets
    ctx.prior_results["I03"] = rec_i03
    rec_i04 = await i04.execute("case_cap_02", ev_pos, ctx)
    assert rec_i04.status == EngineExecutionResult.SUCCESS
    assert rec_i04.outputs[0]["track_id"] == "TRK_PERSON_01"

    # Edge: no person detections
    rec_empty_i03 = EngineExecutionRecord(case_id="case_cap_02", engine_id="I03", engine_version="1.0.0", execution_mode="MODEL", outputs=[])
    ctx_empty = EngineContext(case_id="case_cap_02", prior_results={"I03": rec_empty_i03})
    rec_no_person = await i04.execute("case_cap_02", ev_pos, ctx_empty)
    assert rec_no_person.status == EngineExecutionResult.NO_USABLE_OUTPUT


@pytest.mark.asyncio
async def test_i05_vehicle_tracking():
    i05 = engine_registry.get("I05")
    ctx_veh = EngineContext(case_id="case_cap_02", specific_offense="VEHICLE_THEFT")
    ev_veh = DummyEvidence("ev_car", "CCTV", metadata={"vehicle_info": {"type": "SUV", "color": "Silver", "plate": "7XYZ99"}})

    rec_veh = await i05.execute("case_cap_02", ev_veh, ctx_veh)
    assert rec_veh.status == EngineExecutionResult.SUCCESS
    assert rec_veh.outputs[0]["vehicle_type"] == "SUV"

    # Clean scene without vehicle
    ctx_clean = EngineContext(case_id="case_cap_02", specific_offense="SHOPLIFTING")
    ev_no_veh = DummyEvidence("ev_clean", "CCTV", metadata={})
    rec_clean = await i05.execute("case_cap_02", ev_no_veh, ctx_clean)
    assert rec_clean.status == EngineExecutionResult.NO_USABLE_OUTPUT


@pytest.mark.asyncio
async def test_i06_appearance_and_i07_candidate_reid():
    i06 = engine_registry.get("I06")
    i07 = engine_registry.get("I07")
    ctx = EngineContext(case_id="case_cap_02")
    ev = DummyEvidence("ev_cctv", "CCTV")

    rec_i06 = await i06.execute("case_cap_02", ev, ctx)
    assert "upper_clothing_color" in rec_i06.outputs[0]["attributes"]

    ctx.prior_results["I06"] = rec_i06
    rec_i07 = await i07.execute("case_cap_02", ev, ctx)
    assert rec_i07.outputs[0]["linkage_status"] == "CANDIDATE_ONLY"


@pytest.mark.asyncio
async def test_i08_zone_i09_interaction_i10_blind_spot():
    i08 = engine_registry.get("I08")
    i09 = engine_registry.get("I09")
    i10 = engine_registry.get("I10")
    ctx = EngineContext(case_id="case_cap_02")
    ev = DummyEvidence("ev_cctv", "CCTV")

    rec_i08 = await i08.execute("case_cap_02", ev, ctx)
    assert any(z["event_type"] == "ZONE_ENTRY" for z in rec_i08.outputs)

    rec_i09 = await i09.execute("case_cap_02", ev, ctx)
    assert rec_i09.outputs[0]["interaction_type"] == "REACH_AND_RETRIEVE"

    ctx.prior_results["I08"] = rec_i08
    rec_i10 = await i10.execute("case_cap_02", ev, ctx)
    assert rec_i10.outputs[0]["blind_spot_type"] == "FIELD_OF_VIEW_COVERAGE_GAP"


@pytest.mark.asyncio
async def test_i11_witness_and_i12_video_timeline():
    i11 = engine_registry.get("I11")
    i12 = engine_registry.get("I12")
    ctx = EngineContext(case_id="case_cap_02")

    ev_wit = DummyEvidence("ev_wit", "WITNESS_STATEMENT", metadata={"witness_name": "Store Clerk", "narrative": "Saw person take jacket."})
    rec_i11 = await i11.execute("case_cap_02", ev_wit, ctx)
    # I11 is LLM-powered. When no LLM is configured in test env, it MUST return BLOCKED.
    # This is the correct behavior per the NO-AI-FALLBACK POLICY.
    assert rec_i11.status in [EngineExecutionResult.BLOCKED, EngineExecutionResult.SUCCESS], (
        f"I11 must be BLOCKED (no LLM) or SUCCESS (LLM available), got: {rec_i11.status}"
    )
    if rec_i11.status == EngineExecutionResult.BLOCKED:
        # Correct behavior: no synthetic claims produced
        assert len(rec_i11.outputs) == 0, "BLOCKED I11 must produce zero outputs"
        assert "BLOCKED" in rec_i11.actual_execution_path.upper(), (
            f"actual_execution_path must indicate BLOCKED, got: {rec_i11.actual_execution_path}"
        )
    else:
        # LLM was available: check output structure
        assert rec_i11.outputs[0]["credibility_heuristic"] == "FIRST_PARTY_EYEWITNESS"

    # Video timeline synthesizes zone outputs
    i08 = engine_registry.get("I08")
    rec_i08 = await i08.execute("case_cap_02", ev_wit, ctx)
    ctx.prior_results["I08"] = rec_i08
    rec_i12 = await i12.execute("case_cap_02", ev_wit, ctx)
    assert len(rec_i12.outputs) >= 1


# ===========================================================================
# GROUP C: Forensic AI (F01–F09) Capability Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_f01_metadata_f02_quality():
    f01 = engine_registry.get("F01")
    f02 = engine_registry.get("F02")
    ctx = EngineContext(case_id="case_cap_03")

    ev_img = DummyEvidence("ev_photo", "IMAGE", metadata={"sharpness": 150.0})
    rec_f01 = await f01.execute("case_cap_03", ev_img, ctx)
    assert rec_f01.outputs[0]["camera_make"] != ""

    rec_f02 = await f02.execute("case_cap_03", ev_img, ctx)
    assert rec_f02.outputs[0]["clarity_rating"] == "HIGH"

    # Degraded sharpness
    ev_blur = DummyEvidence("ev_blur", "IMAGE", metadata={"sharpness": 25.0})
    rec_f02_blur = await f02.execute("case_cap_03", ev_blur, ctx)
    assert rec_f02_blur.outputs[0]["clarity_rating"] == "POOR"
    assert rec_f02_blur.outputs[0]["motion_blur_detected"] is True


@pytest.mark.asyncio
async def test_f03_scene_objects_f04_damage_f05_barriers_f06_toolmarks():
    f03 = engine_registry.get("F03")
    f04 = engine_registry.get("F04")
    f05 = engine_registry.get("F05")
    f06 = engine_registry.get("F06")
    ctx = EngineContext(case_id="case_cap_03")
    ev = DummyEvidence("ev_photo", "IMAGE")

    rec_f03 = await f03.execute("case_cap_03", ev, ctx)
    assert any(o["category"] == "ENTRYWAY_DOOR" for o in rec_f03.outputs)

    rec_f04 = await f04.execute("case_cap_03", ev, ctx)
    assert rec_f04.outputs[0]["damage_category"] == "MECHANICAL_PRY_DEFORMATION"

    rec_f05 = await f05.execute("case_cap_03", ev, ctx)
    assert rec_f05.outputs[0]["barrier_status"] == "COMPROMISED_EXTERIOR_LATCH"

    rec_f06 = await f06.execute("case_cap_03", ev, ctx)
    assert "PRY_LEVER_IMPRESSION" in rec_f06.outputs[0]["impression_type"]


@pytest.mark.asyncio
async def test_f07_comparison_f08_acoustic_f09_speech():
    f07 = engine_registry.get("F07")
    f08 = engine_registry.get("F08")
    f09 = engine_registry.get("F09")
    ctx = EngineContext(case_id="case_cap_03")
    ev = DummyEvidence("ev_audio", "AUDIO")

    rec_f07 = await f07.execute("case_cap_03", ev, ctx)
    assert rec_f07.outputs[0]["structural_similarity_index"] > 0

    rec_f08 = await f08.execute("case_cap_03", ev, ctx)
    assert rec_f08.outputs[0]["signal_to_noise_ratio_db"] > 0

    rec_f09 = await f09.execute("case_cap_03", ev, ctx)
    assert rec_f09.outputs[0]["sound_class"] == "METALLIC_IMPACT"


# ===========================================================================
# GROUP D: Financial AI (FI01–FI07) Capability Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_fi01_parser_fi02_reconciliation_exact_and_discrepancy():
    fi01 = engine_registry.get("FI01")
    fi02 = engine_registry.get("FI02")
    ctx = EngineContext(case_id="case_cap_04")

    # Discrepancy scenario
    ev_disc = DummyEvidence("ev_inv", "INVENTORY_RECORD", metadata={
        "inventory_items": [
            {"sku": "SKU-01", "product_name": "Watch", "expected_stock_count": 10, "physical_count": 8, "unit_cost_usd": 150.0}
        ]
    })
    rec_fi01 = await fi01.execute("case_cap_04", ev_disc, ctx)
    ctx.prior_results["FI01"] = rec_fi01

    rec_fi02 = await fi02.execute("case_cap_04", ev_disc, ctx)
    assert rec_fi02.outputs[0]["total_missing_units"] == 2
    assert rec_fi02.outputs[0]["total_shrinkage_usd"] == 300.0

    # Exact match scenario (zero shrink)
    ev_exact = DummyEvidence("ev_exact", "INVENTORY_RECORD", metadata={
        "inventory_items": [
            {"sku": "SKU-01", "product_name": "Watch", "expected_stock_count": 10, "physical_count": 10, "unit_cost_usd": 150.0}
        ]
    })
    rec_exact_01 = await fi01.execute("case_cap_04", ev_exact, ctx)
    ctx.prior_results["FI01"] = rec_exact_01
    rec_exact_02 = await fi02.execute("case_cap_04", ev_exact, ctx)
    assert rec_exact_02.outputs[0]["total_missing_units"] == 0
    assert rec_exact_02.outputs[0]["total_shrinkage_usd"] == 0.0


@pytest.mark.asyncio
async def test_fi03_sku_fi04_pos_fi05_matcher_fi06_anomalies_fi07_alternative():
    fi03 = engine_registry.get("FI03")
    fi04 = engine_registry.get("FI04")
    fi05 = engine_registry.get("FI05")
    fi06 = engine_registry.get("FI06")
    fi07 = engine_registry.get("FI07")
    ctx = EngineContext(case_id="case_cap_04")
    ev = DummyEvidence("ev_pos", "TRANSACTION_RECORD")

    rec_fi03 = await fi03.execute("case_cap_04", ev, ctx)
    assert "upc_barcode" in rec_fi03.outputs[0]

    rec_fi04 = await fi04.execute("case_cap_04", ev, ctx)
    assert len(rec_fi04.outputs) >= 1

    rec_fi05 = await fi05.execute("case_cap_04", ev, ctx)
    assert "unexplained_shrink_items" in rec_fi05.outputs[0]

    rec_fi06 = await fi06.execute("case_cap_04", ev, ctx)
    assert rec_fi06.outputs[0]["event_type"] == "MANUAL_DRAWER_OPEN_NO_SALE"

    rec_fi07 = await fi07.execute("case_cap_04", ev, ctx)
    assert len(rec_fi07.outputs[0]["alternative_explanations_evaluated"]) >= 2


# ===========================================================================
# GROUP E & F: Intelligence & Reconstruction Capability Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_x01_candidate_entity_resolution_decoupled():
    x01 = engine_registry.get("X01")
    ctx = EngineContext(case_id="case_cap_05")
    rec = await x01.execute("case_cap_05", None, ctx)
    assert rec.status == EngineExecutionResult.SUCCESS
    p1 = next((e for e in rec.outputs if e["entity_type"] == "PERSON"), None)
    assert p1 is not None
    assert p1["identity_status"] == "CANDIDATE" # Strictly candidate


@pytest.mark.asyncio
async def test_x02_source_timelines_decoupled():
    x02 = engine_registry.get("X02")
    ctx = EngineContext(case_id="case_cap_05")
    rec = await x02.execute("case_cap_05", None, ctx)
    assert rec.status == EngineExecutionResult.SUCCESS
    assert len(rec.outputs) >= 1


@pytest.mark.asyncio
async def test_x06_evidence_sufficiency_states():
    x06 = engine_registry.get("X06")

    # State 1: No real Investigation engines ran (all BLOCKED/absent) → INSUFFICIENT_FOR_RECONSTRUCTION
    ctx_empty = EngineContext(case_id="c2", prior_results={})
    rec_empty = await x06.execute("c2", None, ctx_empty)
    assert rec_empty.outputs[0]["sufficiency_rating"] == "INSUFFICIENT_FOR_RECONSTRUCTION", (
        f"X06 with no real engines must be INSUFFICIENT, got: {rec_empty.outputs[0]['sufficiency_rating']}"
    )
    assert rec_empty.outputs[0]["proceed_to_reconstruction"] is False

    # State 2: Only X03 cross-domain correlation (no I-engine outputs) → still INSUFFICIENT
    x03_mock = EngineExecutionRecord(case_id="c1", engine_id="X03", engine_version="1.0.0", execution_mode="HYBRID", outputs=[{"corr": "1"}])
    ctx_suff = EngineContext(case_id="c1", prior_results={"X03": x03_mock})
    rec_suff = await x06.execute("c1", None, ctx_suff)
    # Still INSUFFICIENT because no I-engine (I01-I12) succeeded with real outputs
    assert rec_suff.outputs[0]["sufficiency_rating"] == "INSUFFICIENT_FOR_RECONSTRUCTION", (
        f"X06 with only X03 (no I-engine) must still be INSUFFICIENT, got: {rec_suff.outputs[0]['sufficiency_rating']}"
    )

    # State 3: CCTV Investigation engine present → SUFFICIENT
    from app.department_engines.framework.base import EngineExecutionResult as EER
    i01_mock = EngineExecutionRecord(case_id="c3", engine_id="I01", engine_version="1.0.0", execution_mode="DETERMINISTIC",
                                     outputs=[{"duration_seconds": 300}], status=EER.SUCCESS)
    i12_mock = EngineExecutionRecord(case_id="c3", engine_id="I12", engine_version="1.0.0", execution_mode="DETERMINISTIC",
                                     outputs=[{"event_name": "INGRESS"}], status=EER.SUCCESS)
    x02_mock = EngineExecutionRecord(case_id="c3", engine_id="X02", engine_version="1.0.0", execution_mode="DETERMINISTIC",
                                     outputs=[{"event_id": "TL_CCTV_1", "source_modality": "CCTV_VIDEO", "timestamp": "2026-01-01T10:00:00Z"}],
                                     status=EER.SUCCESS)
    ctx_video = EngineContext(case_id="c3", prior_results={"I01": i01_mock, "I12": i12_mock, "X02": x02_mock})
    rec_video = await x06.execute("c3", None, ctx_video)
    assert rec_video.outputs[0]["sufficiency_rating"] == "SUFFICIENT_FOR_RECONSTRUCTION", (
        f"X06 with CCTV engine should be SUFFICIENT, got: {rec_video.outputs[0]['sufficiency_rating']}"
    )
    assert rec_video.outputs[0]["proceed_to_reconstruction"] is True


@pytest.mark.asyncio
async def test_r01_r02_r03_r04_pipeline():
    r01 = engine_registry.get("R01")
    r02 = engine_registry.get("R02")
    r03 = engine_registry.get("R03")
    r04 = engine_registry.get("R04")

    ctx = EngineContext(case_id="case_cap_06")
    rec_r01 = await r01.execute("case_cap_06", None, ctx)
    # Without evidence, R01 takes the deterministic INSUFFICIENT_EVIDENCE path
    # (X06 is absent → no proceed_to_reconstruction=False → no special block, but no
    # Investigation engine outputs exist, so R01 hits the no-citations branch)
    assert rec_r01.status in [EngineExecutionResult.PARTIAL, EngineExecutionResult.BLOCKED], (
        f"R01 without any evidence/LLM must be PARTIAL or BLOCKED, got: {rec_r01.status}"
    )
    if rec_r01.outputs:
        # If there are outputs, they must be the INSUFFICIENT_EVIDENCE deterministic finding
        assert rec_r01.outputs[0].get("hypothesis_category") in [
            "INSUFFICIENT_EVIDENCE", "PARTIAL_CIRCUMSTANTIAL"
        ], f"R01 without evidence must produce INSUFFICIENT_EVIDENCE, got: {rec_r01.outputs[0].get('hypothesis_category')}"

    ctx.prior_results["R01"] = rec_r01
    rec_r02 = await r02.execute("case_cap_06", None, ctx)
    # Transit velocity feasibility returns NOT_ASSESSABLE when spatial/time inputs missing
    vel_check = next((c for c in rec_r02.outputs if c["check_name"] == "TRANSIT_VELOCITY_FEASIBILITY"), None)
    assert vel_check["status"] == "NOT_ASSESSABLE"

    ctx.prior_results["R02"] = rec_r02
    rec_r03 = await r03.execute("case_cap_06", None, ctx)
    # R03 handles the case where R01 was INSUFFICIENT_EVIDENCE deterministically
    # so it should succeed with a sufficiency failure challenge OR be BLOCKED if R01 was BLOCKED
    assert rec_r03.status in [
        EngineExecutionResult.SUCCESS,
        EngineExecutionResult.BLOCKED
    ], f"R03 must be SUCCESS (deterministic challenge) or BLOCKED (R01 blocked), got: {rec_r03.status}"
    if rec_r03.status == EngineExecutionResult.SUCCESS:
        assert len(rec_r03.outputs) >= 1
        # The valid deterministic challenge for INSUFFICIENT_EVIDENCE
        assert any(
            c.get("challenge_vector") in ["EVIDENTIARY_SUFFICIENCY_FAILURE", "CHAIN_OF_CUSTODY_OF_MERCHANDISE"
                                           , "IDENTITY_UNCERTAINTY"]
            for c in rec_r03.outputs
        ), f"R03 must have a valid challenge_vector, got: {[c.get('challenge_vector') for c in rec_r03.outputs]}"

    ctx.prior_results["R03"] = rec_r03
    rec_r04 = await r04.execute("case_cap_06", None, ctx)
    assert "non_verdict_declaration" in rec_r04.outputs[0]
    assert "REANALYSIS_REQUESTED" in rec_r04.outputs[0]["permitted_actions"]
