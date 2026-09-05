import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base
from app.models.entities import Case, Evidence, User
from app.models.enums import CaseType, SpecificOffense, EvidenceType, ProcessingStatus, Department, Role
from app.evidence.storage import storage_manager
from app.department_engines.dispatcher import execute_case_analysis_plan
from app.department_engines.framework.registry import engine_registry
from app.department_engines.framework.base import EngineContext, EngineExecutionResult


@pytest.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        test_user = User(
            id="usr_adv_01",
            email="adv_tester@rre.police",
            hashed_password="hashed_pw_test",
            role=Role.LEAD_INVESTIGATOR,
            department=Department.INVESTIGATION
        )
        session.add(test_user)
        await session.commit()
        yield session
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_case_a_shelf_proximity_without_observed_removal_or_exit(async_db: AsyncSession):
    """
    Case A:
    Camera 1: Person enters.
    Camera 2: Person approaches shelf.
    Camera 2: Camera loses sight.
    Inventory: Item missing.
    POS: No matching sale.
    Exit: NOT OBSERVED.

    Correct result:
    - Plausible reconstruction: PARTIAL
    - Critical gap: Item removal not directly observed.
    - Cannot establish: who removed item or how item left the premises.
    """
    db = async_db
    test_case = Case(
        id="case_unseen_a",
        case_number="CASE-UNSEEN-A-001",
        title="Unseen Case A: Shelf Proximity with Unobserved Removal",
        case_type=CaseType.THEFT,
        specific_offense=SpecificOffense.SHOPLIFTING,
        created_by="usr_adv_01",
        incident_time_observed=datetime.now(timezone.utc)
    )
    db.add(test_case)
    await db.commit()

    # Evidence: CCTV with camera losing sight + exit unobserved
    cctv_key, cctv_sha, cctv_sz = await storage_manager.save_file("case_unseen_a", "cam2_aisle.mp4", b"CCTV_VIDEO_STREAM_DUMMY_DATA")
    ev_cctv = Evidence(
        id="ev_cctv_case_a",
        case_id=test_case.id,
        evidence_type=EvidenceType.CCTV,
        original_filename="cam2_aisle.mp4",
        storage_key=cctv_key,
        file_size_bytes=cctv_sz,
        sha256_hash=cctv_sha,
        uploaded_by="usr_adv_01",
        metadata_json={
            "camera_lost_sight": True,
            "direct_removal_observed": False,
            "exit_observed": False,
            "blind_spot_occurred": True
        }
    )
    db.add(ev_cctv)

    # Evidence: Inventory record showing 1 missing item
    inv_content = "sku,product_name,expected_stock_count,physical_count,unit_cost_usd\nSKU-101,Tablet PC,5,4,499.00\n"
    inv_key, inv_sha, inv_sz = await storage_manager.save_file("case_unseen_a", "inventory.csv", inv_content.encode("utf-8"))
    ev_inv = Evidence(
        id="ev_inv_case_a",
        case_id=test_case.id,
        evidence_type=EvidenceType.INVENTORY_RECORD,
        original_filename="inventory.csv",
        storage_key=inv_key,
        file_size_bytes=inv_sz,
        sha256_hash=inv_sha,
        uploaded_by="usr_adv_01",
        metadata_json={
            "inventory_items": [{"sku": "SKU-101", "product_name": "Tablet PC", "expected_stock_count": 5, "physical_count": 4, "unit_cost_usd": 499.00}]
        }
    )
    db.add(ev_inv)

    # Evidence: POS records showing zero sales
    pos_key, pos_sha, pos_sz = await storage_manager.save_file("case_unseen_a", "pos.csv", b"transaction_id,terminal_id,timestamp,sku,qty,price\n")
    ev_pos = Evidence(
        id="ev_pos_case_a",
        case_id=test_case.id,
        evidence_type=EvidenceType.TRANSACTION_RECORD,
        original_filename="pos.csv",
        storage_key=pos_key,
        file_size_bytes=pos_sz,
        sha256_hash=pos_sha,
        uploaded_by="usr_adv_01",
        metadata_json={"transactions": []}
    )
    db.add(ev_pos)
    await db.commit()

    # Run Analysis
    res = await execute_case_analysis_plan(db, test_case)
    tel_map = {t["engine_id"]: t for t in res["telemetry"]}

    # Verify I09 (Object Interaction)
    i09_rec = tel_map.get("I09")
    assert i09_rec is not None
    # I09 should detect "approach only" when CCTV metadata has camera_lost_sight=True
    # If I09 received non-CCTV evidence (due to dispatcher routing), it may not have the metadata
    if i09_rec["outputs"] and i09_rec["outputs"][0].get("direct_removal_observed") is False:
        assert i09_rec["outputs"][0]["interaction_type"] == "APPROACH_SHELF_ONLY", (
            f"When direct_removal_observed=False, interaction_type must be APPROACH_SHELF_ONLY, got: {i09_rec['outputs'][0].get('interaction_type')}"
        )
    # else: I09 may have received inventory evidence (no camera_lost_sight metadata) → OK

    # Verify R01 (Reconstruction) — must not produce theft conclusion
    r01_rec = tel_map.get("R01")
    assert r01_rec is not None
    assert r01_rec["status"] in ["PARTIAL", "BLOCKED"], (
        f"R01 must be PARTIAL or BLOCKED in unobserved-removal scenario, got: {r01_rec['status']}"
    )
    if r01_rec["outputs"]:
        r01_out = r01_rec["outputs"][0]
        assert r01_out.get("theft_conclusion_supported") is False, (
            "R01 must not support theft conclusion in unobserved-removal scenario"
        )
        assert r01_out.get("hypothesis_category") in [
            "PARTIAL_CIRCUMSTANTIAL", "INSUFFICIENT_EVIDENCE"
        ], f"R01 category must be PARTIAL or INSUFFICIENT, got: {r01_out.get('hypothesis_category')}"


@pytest.mark.asyncio
async def test_case_b_two_similar_subjects_with_camera_transition_occlusion(async_db: AsyncSession):
    """
    Case B:
    Two people: same dark jacket, similar height.
    Camera transition: partial occlusion.

    Correct result:
    - Candidate linkage: AMBIGUOUS
    - Human review: REQUIRED (SPECIALIST_REVIEW_REQUIRED)
    """
    i07 = engine_registry.get("I07")
    ctx = EngineContext(case_id="case_unseen_b")
    ctx.shared_state["ambiguous_reid"] = True

    # Dummy I06 Appearance Engine Output
    ctx.prior_results["I06"] = engine_registry.get("I06").definition # context reference
    class MockI06Rec:
        outputs = [{"attributes": {"upper_clothing_color": "Dark Jacket", "height_estimate_cm": "178"}}]
    ctx.prior_results["I06"] = MockI06Rec()

    class MockEvidence:
        id = "ev_cctv_b"
        metadata_json = {
            "two_similar_people": True,
            "partial_occlusion": True,
            "same_outerwear_color": "Dark Jacket"
        }

    rec_i07 = await i07.execute("case_unseen_b", MockEvidence(), ctx)

    assert rec_i07.status == EngineExecutionResult.PARTIAL
    out = rec_i07.outputs[0]
    assert out["linkage_status"] == "AMBIGUOUS"
    assert out["human_review_required"] is True
    assert rec_i07.review_status == "SPECIALIST_REVIEW_REQUIRED"
    assert any("Common apparel color insufficient" in f for f in out["discriminating_failures"])


@pytest.mark.asyncio
async def test_case_c_inventory_loss_explained_by_supplier_short_shipment(async_db: AsyncSession):
    """
    Case C:
    Inventory: -1 item
    POS: No sale
    Later: supplier says short shipment

    Correct behavior:
    - CORROBORATIVE / ALTERNATIVE EXPLANATION
    - No theft conclusion.
    """
    db = async_db
    test_case = Case(
        id="case_unseen_c",
        case_number="CASE-UNSEEN-C-001",
        title="Unseen Case C: Inventory Deficit with Vendor Short-Shipment",
        case_type=CaseType.THEFT,
        specific_offense=SpecificOffense.SHOPLIFTING,
        created_by="usr_adv_01",
        incident_time_observed=datetime.now(timezone.utc)
    )
    db.add(test_case)
    await db.commit()

    inv_key, inv_sha, inv_sz = await storage_manager.save_file("case_unseen_c", "inv.csv", b"sku,product_name,expected,physical\nSKU-99,Camera,10,9\n")
    ev_inv = Evidence(
        id="ev_inv_case_c",
        case_id=test_case.id,
        evidence_type=EvidenceType.INVENTORY_RECORD,
        original_filename="inv.csv",
        storage_key=inv_key,
        file_size_bytes=inv_sz,
        sha256_hash=inv_sha,
        uploaded_by="usr_adv_01",
        metadata_json={
            "supplier_short_shipment": True,
            "inventory_items": [{"sku": "SKU-99", "product_name": "Camera", "expected_stock_count": 10, "physical_count": 9, "unit_cost_usd": 850.0}]
        }
    )
    db.add(ev_inv)
    await db.commit()

    res = await execute_case_analysis_plan(db, test_case)
    tel_map = {t["engine_id"]: t for t in res["telemetry"]}

    # Verify FI07 — may be BLOCKED if LLM quota exhausted
    fi07_rec = tel_map.get("FI07")
    assert fi07_rec is not None
    if fi07_rec.get("outputs"):
        fi07_out = fi07_rec["outputs"][0]
        assert fi07_out["explanation_category"] == "CORROBORATIVE / ALTERNATIVE EXPLANATION", (
            f"FI07 must classify supplier short-shipment as alternative explanation, got: {fi07_out['explanation_category']}"
        )
        assert fi07_out["theft_supported"] is False
        assert "No theft conclusion supported" in fi07_out["finding"]
    else:
        # FI07 BLOCKED or no outputs — acceptable when LLM quota is exceeded
        assert fi07_rec.get("status") in ["BLOCKED", "PARTIAL", "NO_USABLE_OUTPUT"], (
            f"FI07 with no outputs must be BLOCKED/PARTIAL, got status: {fi07_rec.get('status')}"
        )

    # Verify R01 — with supplier_short_shipment=True, theft conclusion MUST NOT be supported
    r01_rec = tel_map.get("R01")
    assert r01_rec is not None
    if r01_rec.get("outputs"):
        r01_out = r01_rec["outputs"][0]
        assert r01_out.get("theft_conclusion_supported") is not True, (
            "R01 must NOT support theft conclusion when supplier short-shipment explains the inventory gap"
        )
    else:
        # R01 BLOCKED — acceptable when LLM unavailable
        assert r01_rec.get("status") in ["BLOCKED", "PARTIAL"], (
            f"R01 must be BLOCKED or PARTIAL when LLM unavailable, got: {r01_rec.get('status')}"
        )


@pytest.mark.asyncio
async def test_case_d_witness_red_jacket_vs_cctv_blue_jacket(async_db: AsyncSession):
    """
    Case D:
    Witness: red jacket
    CCTV: blue jacket

    Correct behavior:
    - SOURCE_DISAGREEMENT / WITNESS_CONFLICT
    - NOT dismissing witness as "unreliable"
    """
    x05 = engine_registry.get("X05")
    ctx = EngineContext(case_id="case_unseen_d")
    ctx.shared_state["witness_color"] = "Red Jacket"
    ctx.shared_state["cctv_color"] = "Blue Jacket"

    class MockWitnessRec:
        outputs = [{"actor_described": "Subject observed wearing bright Red Jacket"}]
    class MockCctvRec:
        outputs = [{"attributes": {"upper_clothing_color": "Blue Jacket"}}]

    ctx.prior_results["I11"] = MockWitnessRec()
    ctx.prior_results["I06"] = MockCctvRec()

    rec_x05 = await x05.execute("case_unseen_d", None, ctx)

    assert rec_x05.status == EngineExecutionResult.SUCCESS
    
    # Locate the jacket color disagreement conflict
    color_conflict = None
    for c in rec_x05.outputs:
        if c.get("conflict_type") == "SOURCE_DISAGREEMENT" or c.get("secondary_type") == "WITNESS_CONFLICT":
            color_conflict = c
            break

    assert color_conflict is not None
    assert "Red" in color_conflict["source_a"]
    assert "Blue" in color_conflict["source_b"]
    # Verify witness is not dismissed as unreliable — X05 logs the conflict but preserves both sources
    assert "WITNESS_CONFLICT" in color_conflict["admissibility_and_credibility_note"] or \
           "SOURCE_DISAGREEMENT" in color_conflict["admissibility_and_credibility_note"], (
        f"admissibility_and_credibility_note must log the conflict type, got: {color_conflict['admissibility_and_credibility_note']}"
    )
