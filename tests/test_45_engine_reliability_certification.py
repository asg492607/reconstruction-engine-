import pytest
import asyncio
from datetime import datetime, timezone, timedelta

from app.department_engines.framework.registry import engine_registry
from app.department_engines.framework.planner import dynamic_planner
from app.department_engines.framework.validator import output_validator
from app.department_engines.framework.base import (
    EngineContext,
    EngineExecutionRecord,
    EngineExecutionResult,
    ExecutionMode
)

class ScenarioEvidence:
    def __init__(self, id, evidence_type, filename, metadata=None, sha="valid_sha", size=1048576):
        self.id = id
        self.evidence_type = evidence_type
        self.original_filename = filename
        self.file_path = filename
        self.file_size_bytes = size
        self.mime_type = "video/mp4" if evidence_type == "CCTV" else ("text/csv" if "csv" in filename else "image/jpeg")
        self.sha256_hash = sha
        self.created_at = datetime.now(timezone.utc)
        self.metadata_json = metadata or {}


# ---------------------------------------------------------------------------
# Scenario 1: Clear Shoplifting
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_01_clear_shoplifting():
    exhibits = [
        ScenarioEvidence("ev1", "CCTV", "aisle_cam.mp4", metadata={"interactions": [{"type": "CONCEALMENT", "confidence": 0.92}]}),
        ScenarioEvidence("ev2", "INVENTORY_RECORD", "stock.csv", metadata={"inventory_items": [{"sku": "SKU-99", "expected_stock_count": 10, "physical_count": 9, "unit_cost_usd": 200.0}]}),
        ScenarioEvidence("ev3", "TRANSACTION_RECORD", "pos_log.csv", metadata={"transactions": []})
    ]
    plan = dynamic_planner.generate_plan("case_s1", exhibits, specific_offense="SHOPLIFTING")
    assert "I03" in plan.required_engines
    assert "FI02" in plan.required_engines
    assert "X06" in plan.required_engines

    # Reconcile and correlate
    fi02 = engine_registry.get("FI02")
    ctx = EngineContext(case_id="case_s1")
    fi01_rec = EngineExecutionRecord(case_id="case_s1", engine_id="FI01", engine_version="1.0.0", execution_mode="DETERMINISTIC", outputs=[{"sku": "SKU-99", "expected_stock_count": 10, "physical_count": 9, "unit_cost_usd": 200.0}])
    ctx.prior_results["FI01"] = fi01_rec
    rec_reconcile = await fi02.execute("case_s1", exhibits[1], ctx)
    assert rec_reconcile.outputs[0]["total_missing_units"] == 1


# ---------------------------------------------------------------------------
# Scenario 2: Ambiguous Shoplifting (Loitering without visual concealment)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_02_ambiguous_shoplifting():
    x05 = engine_registry.get("X05")
    ctx = EngineContext(case_id="case_s2")
    rec_conf = await x05.execute("case_s2", None, ctx)
    unc = next((c for c in rec_conf.outputs if c["conflict_type"] == "UNCERTAINTY"), None)
    assert unc is not None
    assert unc["severity"] == "MEDIUM"


# ---------------------------------------------------------------------------
# Scenario 3: Employee Theft (Internal stock discrepancy)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_03_employee_theft():
    fi06 = engine_registry.get("FI06")
    ctx = EngineContext(case_id="case_s3", specific_offense="EMPLOYEE_THEFT")
    rec_irr = await fi06.execute("case_s3", None, ctx)
    assert rec_irr.outputs[0]["event_type"] == "MANUAL_DRAWER_OPEN_NO_SALE"


# ---------------------------------------------------------------------------
# Scenario 4: Commercial Burglary (Forced entry & broken barrier)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_04_commercial_burglary():
    exhibits = [ScenarioEvidence("ev_photo", "IMAGE", "shattered_backdoor.jpg", metadata={"damage": {"damage_category": "FORCED_PRY"}})]
    plan = dynamic_planner.generate_plan("case_s4", exhibits, specific_offense="BURGLARY_THEFT")
    assert "F04" in plan.required_engines
    assert "F05" in plan.required_engines

    f04 = engine_registry.get("F04")
    ctx = EngineContext(case_id="case_s4")
    rec_dmg = await f04.execute("case_s4", exhibits[0], ctx)
    assert rec_dmg.status == EngineExecutionResult.SUCCESS


# ---------------------------------------------------------------------------
# Scenario 5: Armed Commercial Robbery
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_05_armed_robbery():
    exhibits = [
        ScenarioEvidence("ev_cctv", "CCTV", "counter.mp4"),
        ScenarioEvidence("ev_wit", "WITNESS_STATEMENT", "teller_statement.txt", metadata={"narrative": "Subject brandished handgun at register."})
    ]
    plan = dynamic_planner.generate_plan("case_s5", exhibits, specific_offense="ARMED_ROBBERY")
    assert "I11" in plan.required_engines
    assert "I03" in plan.required_engines


# ---------------------------------------------------------------------------
# Scenario 6: Vehicle Theft
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_06_vehicle_theft():
    exhibits = [
        ScenarioEvidence("ev_cctv", "CCTV", "parking_gate.mp4"),
        ScenarioEvidence("ev_veh", "VEHICLE_RECORD", "stolen_vin_report.pdf")
    ]
    plan = dynamic_planner.generate_plan("case_s6", exhibits, specific_offense="VEHICLE_THEFT")
    assert "I05" in plan.required_engines

    i05 = engine_registry.get("I05")
    ctx = EngineContext(case_id="case_s6", specific_offense="VEHICLE_THEFT")
    rec = await i05.execute("case_s6", exhibits[0], ctx)
    assert rec.status == EngineExecutionResult.SUCCESS
    assert rec.outputs[0]["speed_estimate_kph"] > 0


# ---------------------------------------------------------------------------
# Scenario 7: Cargo Theft
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_07_cargo_theft():
    exhibits = [
        ScenarioEvidence("ev_dock", "CCTV", "loading_bay.mp4"),
        ScenarioEvidence("ev_inv", "INVENTORY_RECORD", "pallet_manifest.csv")
    ]
    plan = dynamic_planner.generate_plan("case_s7", exhibits, specific_offense="CARGO_THEFT")
    assert "I08" in plan.required_engines
    assert "FI02" in plan.required_engines


# ---------------------------------------------------------------------------
# Scenario 8: CCTV-Only Investigation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_08_cctv_only():
    exhibits = [ScenarioEvidence("ev1", "CCTV", "store.mp4")]
    plan = dynamic_planner.generate_plan("case_s8", exhibits)
    assert "I03" in plan.required_engines
    unavail = {u["engine_id"] for u in plan.unavailable_engines}
    assert "FI01" in unavail # Financial unavailable
    assert "I11" in unavail  # Witness unavailable
    assert "X06" in plan.required_engines # Intelligence still resolves


# ---------------------------------------------------------------------------
# Scenario 9: Witness-Only Investigation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_09_witness_only():
    exhibits = [ScenarioEvidence("ev_wit", "WITNESS_STATEMENT", "statement.txt")]
    plan = dynamic_planner.generate_plan("case_s9", exhibits)
    assert "I11" in plan.required_engines
    unavail = {u["engine_id"] for u in plan.unavailable_engines}
    assert "I01" in unavail # Video unavailable
    assert "FI01" in unavail


# ---------------------------------------------------------------------------
# Scenario 10: Financial / Inventory-Only Investigation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_10_financial_only():
    exhibits = [
        ScenarioEvidence("ev_inv", "INVENTORY_RECORD", "stock.csv"),
        ScenarioEvidence("ev_pos", "TRANSACTION_RECORD", "pos.csv")
    ]
    plan = dynamic_planner.generate_plan("case_s10", exhibits)
    assert "FI01" in plan.required_engines
    assert "FI04" in plan.required_engines
    unavail = {u["engine_id"] for u in plan.unavailable_engines}
    assert "I01" in unavail # No CCTV


# ---------------------------------------------------------------------------
# Scenario 11: Conflicting CCTV Timestamps (Clock Drift)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_11_clock_drift():
    x05 = engine_registry.get("X05")
    ctx = EngineContext(case_id="case_s11")
    rec = await x05.execute("case_s11", None, ctx)
    temp_disc = next((c for c in rec.outputs if c["conflict_type"] == "TEMPORAL_DISCREPANCY"), None)
    assert temp_disc is not None
    assert temp_disc["delta_minutes"] > 0


# ---------------------------------------------------------------------------
# Scenario 12: Camera Blind Spot Gap
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_12_camera_blind_spot():
    i10 = engine_registry.get("I10")
    ctx = EngineContext(case_id="case_s12")
    rec = await i10.execute("case_s12", None, ctx)
    assert rec.outputs[0]["unmonitored_distance_meters"] == 12.5


# ---------------------------------------------------------------------------
# Scenario 13: Similar-Looking People (Candidate Re-ID Ambiguity)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_13_similar_looking_people():
    i07 = engine_registry.get("I07")
    i06_rec = EngineExecutionRecord(case_id="case_s13", engine_id="I06", engine_version="1.0.0", execution_mode="MODEL", outputs=[{"attributes": {"clothing": "Dark"}}])
    ctx = EngineContext(case_id="case_s13", prior_results={"I06": i06_rec})
    rec = await i07.execute("case_s13", None, ctx)
    assert rec.outputs[0]["linkage_status"] == "CANDIDATE_ONLY"


# ---------------------------------------------------------------------------
# Scenario 14: Poor-Quality Video
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_14_poor_quality_video():
    e03 = engine_registry.get("E03")
    ev_poor = ScenarioEvidence("ev_low", "CCTV", "low_bitrate.mp4", size=30_000)
    ctx = EngineContext(case_id="case_s14")
    rec = await e03.execute("case_s14", ev_poor, ctx)
    assert rec.outputs[0]["quality_grade"] == "LOW"


# ---------------------------------------------------------------------------
# Scenario 15: Missing Evidence & Gaps
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_15_missing_evidence():
    x04 = engine_registry.get("X04")
    ctx = EngineContext(case_id="case_s15")
    rec = await x04.execute("case_s15", None, ctx)
    assert any(g["gap_type"] == "SPATIAL_BLIND_SPOT" for g in rec.outputs)


# ---------------------------------------------------------------------------
# Scenario 16: Conflicting Departments (Witness vs Camera)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_16_conflicting_departments():
    x05 = engine_registry.get("X05")
    ctx = EngineContext(case_id="case_s16")
    rec = await x05.execute("case_s16", None, ctx)
    wit_conf = next((c for c in rec.outputs if c["conflict_type"] == "WITNESS_CONFLICT"), None)
    assert wit_conf is not None


# ---------------------------------------------------------------------------
# Scenario 17: Benign Alternative Explanation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_17_benign_alternative():
    fi07 = engine_registry.get("FI07")
    ctx = EngineContext(case_id="case_s17")
    rec = await fi07.execute("case_s17", None, ctx)
    alts = rec.outputs[0]["alternative_explanations_evaluated"]
    assert any("Supplier short-shipment" in a["explanation"] for a in alts)


# ---------------------------------------------------------------------------
# Scenario 18: No Defensible Reconstruction (Safe Halt)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_18_no_defensible_reconstruction():
    x06 = engine_registry.get("X06")
    r01 = engine_registry.get("R01")
    ctx = EngineContext(case_id="case_s18", prior_results={})

    # X06 evaluates to INSUFFICIENT_FOR_RECONSTRUCTION (correct new enum)
    rec_x06 = await x06.execute("case_s18", None, ctx)
    assert rec_x06.outputs[0]["sufficiency_rating"] == "INSUFFICIENT_FOR_RECONSTRUCTION", (
        f"X06 with no evidence must return INSUFFICIENT_FOR_RECONSTRUCTION, got: {rec_x06.outputs[0]['sufficiency_rating']}"
    )
    assert rec_x06.outputs[0]["proceed_to_reconstruction"] is False

    # R01 halts safely via the INSUFFICIENT_EVIDENCE deterministic path
    ctx.prior_results["X06"] = rec_x06
    rec_r01 = await r01.execute("case_s18", None, ctx)
    assert rec_r01.status in [EngineExecutionResult.PARTIAL, EngineExecutionResult.BLOCKED], (
        f"R01 must halt (PARTIAL or BLOCKED) when evidence is insufficient, got: {rec_r01.status}"
    )
    assert "Halting reconstruction" in (rec_r01.failure_reason or "") or (
        rec_r01.outputs and rec_r01.outputs[0].get("hypothesis_category") == "INSUFFICIENT_EVIDENCE"
    ), f"R01 must express INSUFFICIENT_EVIDENCE, got outputs: {rec_r01.outputs}, failure: {rec_r01.failure_reason}"
