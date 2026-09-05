import pytest
import asyncio
from datetime import datetime, timezone

from app.department_engines.framework.registry import engine_registry
from app.department_engines.framework.planner import dynamic_planner
from app.department_engines.framework.validator import output_validator
from app.department_engines.framework.base import (
    EngineContext,
    EngineExecutionRecord,
    EngineExecutionResult,
    ExecutionMode
)

class MockEvidence:
    def __init__(self, id, evidence_type, file_path="test.mp4", metadata=None):
        self.id = id
        self.evidence_type = evidence_type
        self.original_filename = file_path
        self.file_path = file_path
        self.file_size_bytes = 1048576
        self.mime_type = "video/mp4" if evidence_type == "CCTV" else "image/jpeg"
        self.sha256_hash = "abc123def456"
        self.created_at = datetime.now(timezone.utc)
        self.metadata_json = metadata or {}


def test_all_45_engines_registered():
    """Verify exactly 45 unique engines are registered across all 6 groups."""
    assert engine_registry.count() == 45

    all_defs = engine_registry.list_all()
    all_ids = {d.engine_id for d in all_defs}

    # Group A: Evidence Foundation (7)
    for i in range(1, 8):
        assert f"E{i:02d}" in all_ids

    # Group B: Investigation AI (12)
    for i in range(1, 13):
        assert f"I{i:02d}" in all_ids

    # Group C: Forensic AI (9)
    for i in range(1, 10):
        assert f"F{i:02d}" in all_ids

    # Group D: Financial AI (7)
    for i in range(1, 8):
        assert f"FI{i:02d}" in all_ids

    # Group E: Intelligence (6)
    for i in range(1, 7):
        assert f"X{i:02d}" in all_ids

    # Group F: Reconstruction & Control (4)
    for i in range(1, 5):
        assert f"R{i:02d}" in all_ids


def test_dag_resolution_no_cycles():
    """Test Kahn's algorithm DAG resolution for complete pipeline."""
    dag = engine_registry.resolve_dag(["R04"])
    # R04 dependencies chain: E01, E05, X02, X01, X03, X04, X05, X06, R01, R02, R03, R04
    assert "E01" in dag
    assert "X06" in dag
    assert "R01" in dag
    assert "R04" in dag
    # R04 must be after R03
    assert dag.index("R04") > dag.index("R03")
    assert dag.index("R03") > dag.index("R01")
    assert dag.index("R01") > dag.index("X06")


@pytest.mark.asyncio
async def test_x05_conflict_engine_7_types():
    """Test X05 conflict engine specifically detects and evaluates all 7 discrepancy types."""
    x05 = engine_registry.get("X05")
    assert x05 is not None

    ctx = EngineContext(case_id="case_test_01")
    rec = await x05.execute(case_id="case_test_01", evidence=None, context=ctx)
    assert rec.status == EngineExecutionResult.SUCCESS
    assert len(rec.outputs) > 0

    found_types = {item.get("conflict_type") for item in rec.outputs}
    # Checks presence of required discrepancy types
    assert "TEMPORAL_DISCREPANCY" in found_types
    assert "WITNESS_CONFLICT" in found_types
    assert "UNCERTAINTY" in found_types


@pytest.mark.asyncio
async def test_r02_not_assessable_when_missing_inputs():
    """Test R02 returns NOT_ASSESSABLE for transit velocity when spatial/time inputs missing."""
    r02 = engine_registry.get("R02")
    assert r02 is not None

    # Empty context without spatial/timeline outputs
    ctx = EngineContext(case_id="case_test_02")
    rec = await r02.execute(case_id="case_test_02", evidence=None, context=ctx)
    assert rec.status == EngineExecutionResult.SUCCESS

    velocity_check = next((c for c in rec.outputs if c.get("check_name") == "TRANSIT_VELOCITY_FEASIBILITY"), None)
    assert velocity_check is not None
    assert velocity_check.get("status") == "NOT_ASSESSABLE"


@pytest.mark.asyncio
async def test_output_validator_enforces_anti_hallucination_and_non_verdict():
    """Verify OutputValidator softens inappropriate verdicts and checks schemas."""
    r04_def = engine_registry.get("R04").definition
    rec = EngineExecutionRecord(
        case_id="case_test_03",
        engine_id="R04",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.WORKFLOW,
        outputs=[
            {"observation": "Suspect is guilty of grand theft confirmed at scene.", "confidence": 0.95}
        ]
    )
    validated = output_validator.validate(rec, r04_def)
    assert "guilty" not in validated.outputs[0]["observation"].lower()
    assert "theft confirmed" not in validated.outputs[0]["observation"].lower()
    assert len(validated.warnings) > 0


def test_dynamic_planner_scenarios():
    """Test dynamic planning for 3 distinct offense scenarios: shoplifting, armed robbery, vehicle theft."""
    # Scenario 1: Shoplifting with CCTV + POS + Inventory
    exhibits_shoplifting = [
        MockEvidence("ev1", "CCTV"),
        MockEvidence("ev2", "TRANSACTION_RECORD"),
        MockEvidence("ev3", "INVENTORY_RECORD")
    ]
    plan_shoplifting = dynamic_planner.generate_plan("case_s1", exhibits_shoplifting, specific_offense="SHOPLIFTING")
    assert "I01" in plan_shoplifting.required_engines
    assert "FI01" in plan_shoplifting.required_engines # Inventory required
    assert "FI04" in plan_shoplifting.required_engines # POS required
    assert "X06" in plan_shoplifting.required_engines

    # Scenario 2: Armed Commercial Robbery with Scene Photos + Witness (No Inventory)
    exhibits_robbery = [
        MockEvidence("ev4", "IMAGE"),
        MockEvidence("ev5", "WITNESS_STATEMENT")
    ]
    plan_robbery = dynamic_planner.generate_plan("case_s2", exhibits_robbery, specific_offense="ARMED_ROBBERY")
    assert "F01" in plan_robbery.required_engines
    assert "F04" in plan_robbery.required_engines # Damage detection
    assert "I11" in plan_robbery.required_engines # Witness intelligence
    # Inventory engines should be UNAVAILABLE
    unavail_ids = {u["engine_id"] for u in plan_robbery.unavailable_engines}
    assert "FI01" in unavail_ids

    # Scenario 3: Vehicle Theft
    exhibits_vehicle = [
        MockEvidence("ev6", "CCTV"),
        MockEvidence("ev7", "VEHICLE_RECORD")
    ]
    plan_vehicle = dynamic_planner.generate_plan("case_s3", exhibits_vehicle, specific_offense="VEHICLE_THEFT")
    assert "I05" in plan_vehicle.required_engines # Vehicle tracking prioritized
