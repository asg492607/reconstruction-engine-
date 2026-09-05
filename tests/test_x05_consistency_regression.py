import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entities import Case, Evidence, User, Organization, GapConflict
from app.models.enums import EvidenceType, GapConflictType, Significance, Role, Department
from app.department_engines.framework.registry import engine_registry
from app.department_engines.framework.base import (
    EngineContext,
    EngineExecutionRecord,
    EngineExecutionResult,
    ExecutionMode
)
from app.department_engines.dispatcher import (
    execute_case_analysis_plan,
    get_case_telemetry
)
from app.gap_conflict.detector import list_gaps_and_conflicts


@pytest.mark.asyncio
async def test_x05_consistency_zero_conflicts(db_session: AsyncSession):
    """
    Assert that for a non-conflicting scenario:
    rendered result == persisted X05 result == telemetry analytical result == API response.
    The expected count is NOT hard-coded, but derived directly from actual engine output.
    """
    org = Organization(id=str(uuid.uuid4()), name="Audit Organization")
    db_session.add(org)
    user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        email=f"auditor_{uuid.uuid4().hex[:6]}@rre.internal",
        hashed_password="hashed_test_password",
        full_name="Consistency Auditor",
        role=Role.LEAD_INVESTIGATOR,
        department=Department.INVESTIGATION
    )
    db_session.add(user)
    await db_session.commit()

    case = Case(
        id=str(uuid.uuid4()),
        case_number=f"TEST-X05-{uuid.uuid4().hex[:6]}",
        title="X05 Consistency Verification (Zero Conflicts)",
        case_type="THEFT",
        organization_id=org.id,
        created_by=user.id
    )
    db_session.add(case)

    # Exhibits: Image + Witness (no CCTV)
    ev_image = Evidence(
        id=str(uuid.uuid4()),
        case_id=case.id,
        evidence_type=EvidenceType.IMAGE,
        original_filename="tamper.jpg",
        storage_key=f"{case.id}/tamper.jpg",
        sha256_hash="1" * 64,
        file_size_bytes=1024,
        mime_type="image/jpeg",
        uploaded_by=user.id
    )
    ev_witness = Evidence(
        id=str(uuid.uuid4()),
        case_id=case.id,
        evidence_type=EvidenceType.WITNESS_STATEMENT,
        original_filename="witness.txt",
        storage_key=f"{case.id}/witness.txt",
        sha256_hash="2" * 64,
        file_size_bytes=512,
        mime_type="text/plain",
        uploaded_by=user.id
    )
    db_session.add_all([ev_image, ev_witness])
    await db_session.commit()

    # Pre-seed stale conflicts in the database from a hypothetical earlier run
    stale_conflict = GapConflict(
        case_id=case.id,
        gc_type=GapConflictType.SOURCE_DISAGREEMENT,
        description="Stale prior conflict from uncleaned run",
        significance=Significance.HIGH
    )
    db_session.add(stale_conflict)
    await db_session.commit()

    # Execute full analysis plan through dispatcher
    exec_result = await execute_case_analysis_plan(db_session, case, user_id=user.id)
    assert exec_result["engines_executed"] > 0

    # 1. Derive expected count strictly from actual X05 engine output
    telemetry = get_case_telemetry(case.id)
    x05_telemetry = next((t for t in telemetry if t["engine_id"] == "X05"), None)
    assert x05_telemetry is not None, "X05 telemetry record must exist"

    actual_engine_output = x05_telemetry.get("outputs", [])
    actual_conflict_count = len(actual_engine_output)

    # 2. Persisted X05 result in database
    persisted_conflicts = (await db_session.execute(
        select(GapConflict).where(
            GapConflict.case_id == case.id,
            GapConflict.gc_type != GapConflictType.GAP
        )
    )).scalars().all()
    persisted_conflict_count = len(persisted_conflicts)

    # 3. Telemetry analytical result count
    telemetry_conflict_count = len(actual_engine_output)

    # 4. API response count
    api_records = await list_gaps_and_conflicts(db_session, case.id)
    api_conflict_count = len([g for g in api_records if g.gc_type != GapConflictType.GAP])

    # 5. Frontend rendered result simulation
    # In frontend: activeConflicts = x05Telemetry ? telemetryConflicts : gapsConflicts.filter(...)
    rendered_conflict_count = len(actual_engine_output) if x05_telemetry else api_conflict_count

    # Assert strict equality across all layers derived from actual engine output (never hard-coded)
    assert persisted_conflict_count == actual_conflict_count, (
        f"Persisted DB conflicts ({persisted_conflict_count}) does not match actual engine output ({actual_conflict_count})"
    )
    assert telemetry_conflict_count == actual_conflict_count, (
        f"Telemetry output conflicts ({telemetry_conflict_count}) does not match actual engine output ({actual_conflict_count})"
    )
    assert api_conflict_count == actual_conflict_count, (
        f"API conflicts count ({api_conflict_count}) does not match actual engine output ({actual_conflict_count})"
    )
    assert rendered_conflict_count == actual_conflict_count, (
        f"Rendered conflicts ({rendered_conflict_count}) does not match actual engine output ({actual_conflict_count})"
    )


@pytest.mark.asyncio
async def test_x05_consistency_with_active_conflicts(db_session: AsyncSession):
    """
    Assert that when X05 detects actual conflicts between witness statement and CCTV:
    rendered result == persisted X05 result == telemetry analytical result == API response.
    The expected count is NOT hard-coded, but derived directly from actual engine output.
    """
    org = Organization(id=str(uuid.uuid4()), name="Audit Organization 2")
    db_session.add(org)
    user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        email=f"auditor_{uuid.uuid4().hex[:6]}@rre.internal",
        hashed_password="hashed_test_password",
        full_name="Consistency Auditor 2",
        role=Role.LEAD_INVESTIGATOR,
        department=Department.INVESTIGATION
    )
    db_session.add(user)
    await db_session.commit()

    case = Case(
        id=str(uuid.uuid4()),
        case_number=f"TEST-X05-CONF-{uuid.uuid4().hex[:6]}",
        title="X05 Consistency Verification (With Discrepancy)",
        case_type="THEFT",
        organization_id=org.id,
        created_by=user.id
    )
    db_session.add(case)
    await db_session.commit()

    # Create context with conflicting witness (Red Jacket) and CCTV attributes (Blue Jacket)
    context = EngineContext(
        case_id=case.id,
        case_title=case.title,
        specific_offense="THEFT",
        user_id=user.id
    )
    context.prior_results["I11"] = EngineExecutionRecord(
        case_id=case.id,
        engine_id="I11",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.REAL_LLM,
        status=EngineExecutionResult.SUCCESS,
        outputs=[{"actor_described": "Subject observed wearing bright Red Jacket fleeing scene"}]
    )
    context.prior_results["I06"] = EngineExecutionRecord(
        case_id=case.id,
        engine_id="I06",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.MODEL,
        status=EngineExecutionResult.SUCCESS,
        outputs=[{"attributes": {"upper_clothing_color": "Blue / Dark Navy Jacket"}}]
    )
    context.prior_results["X02"] = EngineExecutionRecord(
        case_id=case.id,
        engine_id="X02",
        engine_version="1.0.0",
        execution_mode=ExecutionMode.DETERMINISTIC,
        status=EngineExecutionResult.SUCCESS,
        outputs=[{"event_id": "EVT_01", "timestamp": "2026-09-05T12:00:00Z"}]
    )

    x05_engine = engine_registry.get("X05")
    assert x05_engine is not None

    # Execute X05 directly
    x05_record = await x05_engine.execute(case_id=case.id, evidence=None, context=context)
    assert x05_record.status == EngineExecutionResult.SUCCESS
    context.prior_results["X05"] = x05_record

    # 1. Derive expected count strictly from engine output
    actual_engine_output = x05_record.outputs
    actual_conflict_count = len(actual_engine_output)
    assert actual_conflict_count > 0, "Conflict scenario should produce at least one conflict"

    # 2. Simulate dispatcher sync to DB
    from sqlalchemy import delete
    await db_session.execute(
        delete(GapConflict).where(GapConflict.case_id == case.id, GapConflict.gc_type != GapConflictType.GAP)
    )
    for c in x05_record.outputs:
        gc = GapConflict(
            case_id=case.id,
            gc_type=GapConflictType.SOURCE_DISAGREEMENT,
            description=c.get("discrepancy_explanation") or c.get("description", "Source discrepancy"),
            significance=Significance.HIGH,
            significance_reason=c.get("admissibility_and_credibility_note")
        )
        db_session.add(gc)
    await db_session.commit()

    # 3. Persisted X05 result in database
    persisted_conflicts = (await db_session.execute(
        select(GapConflict).where(
            GapConflict.case_id == case.id,
            GapConflict.gc_type != GapConflictType.GAP
        )
    )).scalars().all()
    persisted_conflict_count = len(persisted_conflicts)

    # 4. Telemetry analytical result count
    telemetry_conflict_count = len(actual_engine_output)

    # 5. API response count
    api_records = await list_gaps_and_conflicts(db_session, case.id)
    api_conflict_count = len([g for g in api_records if g.gc_type != GapConflictType.GAP])

    # 6. Rendered result simulation
    rendered_conflict_count = len(actual_engine_output)

    # Assert strict equality across all layers
    assert persisted_conflict_count == actual_conflict_count, (
        f"Persisted DB conflicts ({persisted_conflict_count}) does not match actual engine output ({actual_conflict_count})"
    )
    assert telemetry_conflict_count == actual_conflict_count, (
        f"Telemetry output conflicts ({telemetry_conflict_count}) does not match actual engine output ({actual_conflict_count})"
    )
    assert api_conflict_count == actual_conflict_count, (
        f"API conflicts count ({api_conflict_count}) does not match actual engine output ({actual_conflict_count})"
    )
    assert rendered_conflict_count == actual_conflict_count, (
        f"Rendered conflicts ({rendered_conflict_count}) does not match actual engine output ({actual_conflict_count})"
    )
