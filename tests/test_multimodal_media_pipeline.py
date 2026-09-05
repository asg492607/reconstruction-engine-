import pytest
import os
import tempfile
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base
from app.models.entities import Case, Evidence, Observation
from app.models.enums import CaseType, SpecificOffense, EvidenceType, ProcessingStatus, Department
from app.evidence.storage import storage_manager
from app.department_engines.dispatcher import dispatch_evidence_processing, execute_case_analysis_plan, get_case_analysis_plan
from app.department_engines.framework.registry import engine_registry
from app.department_engines.framework.base import EngineExecutionResult


@pytest.fixture
async def async_db_session():
    # Use in-memory SQLite for testing real pipeline
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_multimodal_evidence_pipeline(async_db_session: AsyncSession):
    """
    Validates end-to-end processing of all 6 multimedia file types:
    1. MP4 CCTV video
    2. JPG scene photograph
    3. WAV acoustic audio
    4. CSV inventory ledger
    5. CSV POS transaction stream
    6. TXT witness statement
    through upload -> storage -> classification -> engine execution -> observation creation -> case correlation.
    """
    db = async_db_session

    # 1. Create Test User
    from app.models.entities import User
    from app.models.enums import Role
    test_user = User(
        id="user_test_01",
        email="test_investigator@rre.police",
        hashed_password="dummy_hashed_password",
        full_name="Lead Investigator Test",
        role=Role.LEAD_INVESTIGATOR,
        department=Department.INVESTIGATION
    )
    db.add(test_user)
    await db.commit()

    # 2. Create Case
    test_case = Case(
        id="case_multimodal_001",
        case_number="CASE-MM-2026-001",
        title="Commercial Retail Shoplifting with Forced Emergency Exit",
        case_type=CaseType.THEFT,
        specific_offense=SpecificOffense.SHOPLIFTING,
        incident_location="Flagship Retail Store, Sector 4",
        incident_time_observed=datetime.now(timezone.utc),
        created_by=test_user.id
    )
    db.add(test_case)
    await db.commit()

    # 2. Prepare Multi-Modal Test Media Files
    # (a) MP4 Video (Header bytes + metadata)
    mp4_bytes = b"\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00isommp42" + b"\x00" * 2048
    key_mp4, sha_mp4, size_mp4 = await storage_manager.save_file("case_multimodal_001", "cctv_entrance.mp4", mp4_bytes)
    ev_cctv = Evidence(
        id="ev_mm_cctv",
        case_id=test_case.id,
        evidence_type=EvidenceType.CCTV,
        original_filename="cctv_entrance.mp4",
        storage_key=key_mp4,
        file_size_bytes=size_mp4,
        sha256_hash=sha_mp4,
        mime_type="video/mp4",
        metadata_json={
            "duration_seconds": 180.0,
            "fps": 30.0,
            "resolution": "1920x1080",
            "camera_id": "CAM_ENTRANCE_01",
            "detections": [
                {"class": "person", "confidence": 0.94, "bbox": {"x": 100, "y": 150, "w": 80, "h": 220}},
                {"class": "backpack", "confidence": 0.89, "bbox": {"x": 130, "y": 180, "w": 40, "h": 50}}
            ]
        },
        processing_status=ProcessingStatus.PENDING,
        uploaded_by=test_user.id
    )
    db.add(ev_cctv)

    # (b) JPG Scene Image (JPEG header + bytes)
    jpg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + b"\xaa" * 1024 + b"\xff\xd9"
    key_jpg, sha_jpg, size_jpg = await storage_manager.save_file("case_multimodal_001", "rear_door_damage.jpg", jpg_bytes)
    ev_img = Evidence(
        id="ev_mm_img",
        case_id=test_case.id,
        evidence_type=EvidenceType.IMAGE,
        original_filename="rear_door_damage.jpg",
        storage_key=key_jpg,
        file_size_bytes=size_jpg,
        sha256_hash=sha_jpg,
        mime_type="image/jpeg",
        metadata_json={
            "sharpness": 145.2,
            "camera_make": "Nikon",
            "camera_model": "D850",
            "damage": {
                "damage_category": "MECHANICAL_PRY_DEFORMATION",
                "target_surface": "Rear Steel Latch Plate",
                "severity": "MODERATE"
            }
        },
        processing_status=ProcessingStatus.PENDING,
        uploaded_by=test_user.id
    )
    db.add(ev_img)

    # (c) WAV Audio (RIFF/WAVE header + data)
    wav_bytes = b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00" + b"\x00" * 2048
    key_wav, sha_wav, size_wav = await storage_manager.save_file("case_multimodal_001", "hallway_sensor.wav", wav_bytes)
    ev_aud = Evidence(
        id="ev_mm_aud",
        case_id=test_case.id,
        evidence_type=EvidenceType.AUDIO,
        original_filename="hallway_sensor.wav",
        storage_key=key_wav,
        file_size_bytes=size_wav,
        sha256_hash=sha_wav,
        mime_type="audio/wav",
        metadata_json={
            "sampling_rate": 44100,
            "channels": 1,
            "audio_events": [
                {"sound_class": "METALLIC_IMPACT", "offset_seconds": 45.2, "confidence": 0.91}
            ]
        },
        processing_status=ProcessingStatus.PENDING,
        uploaded_by=test_user.id
    )
    db.add(ev_aud)

    # (d) CSV Inventory Ledger
    csv_inv_content = (
        "sku,product_name,item,category,expected_stock_count,physical_count,delta,status,unit_cost_usd,location_bin\n"
        "SKU-99214,Wireless Noise Cancelling Headphones,Wireless Noise Cancelling Headphones,Electronics,10,7,-3,MISSING,249.99,Aisle 4\n"
        "SKU-48102,Portable Smart Speaker,Portable Smart Speaker,Electronics,15,15,0,VERIFIED,79.99,Aisle 4\n"
    )
    inv_bytes = csv_inv_content.encode("utf-8")
    key_inv, sha_inv, size_inv = await storage_manager.save_file("case_multimodal_001", "inventory_audit.csv", inv_bytes)
    ev_inv = Evidence(
        id="ev_mm_inv",
        case_id=test_case.id,
        evidence_type=EvidenceType.INVENTORY_RECORD,
        original_filename="inventory_audit.csv",
        storage_key=key_inv,
        file_size_bytes=size_inv,
        sha256_hash=sha_inv,
        mime_type="text/csv",
        metadata_json={
            "audit_type": "PHYSICAL_WALL_TO_WALL",
            "inventory_items": [
                {
                    "sku": "SKU-99214",
                    "product_name": "Wireless Noise Cancelling Headphones",
                    "expected_stock_count": 10,
                    "physical_count": 7,
                    "unit_cost_usd": 249.99
                }
            ]
        },
        processing_status=ProcessingStatus.PENDING,
        uploaded_by=test_user.id
    )
    db.add(ev_inv)

    # (e) CSV POS Transactions
    csv_pos_content = (
        "transaction_id,terminal_id,timestamp,sku,qty,price,payment_method,voided\n"
        "TX_1001,REG_01,2026-09-05T14:10:00Z,SKU-48102,1,79.99,CREDIT,false\n"
    )
    pos_bytes = csv_pos_content.encode("utf-8")
    key_pos, sha_pos, size_pos = await storage_manager.save_file("case_multimodal_001", "pos_register_logs.csv", pos_bytes)
    ev_pos = Evidence(
        id="ev_mm_pos",
        case_id=test_case.id,
        evidence_type=EvidenceType.TRANSACTION_RECORD,
        original_filename="pos_register_logs.csv",
        storage_key=key_pos,
        file_size_bytes=size_pos,
        sha256_hash=sha_pos,
        mime_type="text/csv",
        metadata_json={
            "transactions": [
                {
                    "transaction_id": "TX_1001",
                    "terminal_id": "REG_01",
                    "timestamp": "2026-09-05T14:10:00Z",
                    "items": [{"sku": "SKU-48102", "qty": 1, "price": 79.99}]
                }
            ]
        },
        processing_status=ProcessingStatus.PENDING,
        uploaded_by=test_user.id
    )
    db.add(ev_pos)

    # (f) TXT Witness Statement
    txt_wit_content = (
        "WITNESS STATEMENT\n"
        "Name: Sarah Jenkins (Floor Supervisor)\n"
        "Time observed: 14:15:00\n"
        "Statement: I saw an individual wearing a dark jacket and backpack standing near the electronics display. "
        "They walked quickly toward the emergency exit carrying a heavy satchel."
    )
    wit_bytes = txt_wit_content.encode("utf-8")
    key_wit, sha_wit, size_wit = await storage_manager.save_file("case_multimodal_001", "witness_statement_jenkins.txt", wit_bytes)
    ev_wit = Evidence(
        id="ev_mm_wit",
        case_id=test_case.id,
        evidence_type=EvidenceType.WITNESS_STATEMENT,
        original_filename="witness_statement_jenkins.txt",
        storage_key=key_wit,
        file_size_bytes=size_wit,
        sha256_hash=sha_wit,
        mime_type="text/plain",
        metadata_json={
            "witness_name": "Sarah Jenkins",
            "statement_text": txt_wit_content,
            "incident_time_observed": "2026-09-05T14:15:00Z"
        },
        processing_status=ProcessingStatus.PENDING,
        uploaded_by=test_user.id
    )
    db.add(ev_wit)
    await db.commit()

    # 3. Test Direct Single-Evidence Dispatching
    obs_img = await dispatch_evidence_processing(db, test_case, ev_img)
    assert len(obs_img) > 0
    assert any(o.department == Department.FORENSIC for o in obs_img)

    obs_inv = await dispatch_evidence_processing(db, test_case, ev_inv)
    assert len(obs_inv) > 0

    obs_pos = await dispatch_evidence_processing(db, test_case, ev_pos)
    assert len(obs_pos) > 0

    # 4. Test Dynamic Analysis Plan Generation
    plan = await get_case_analysis_plan(db, test_case)
    assert len(plan.required_engines) > 15
    # Verify multi-modal engine inclusion:
    assert "E01" in plan.required_engines
    assert "I03" in plan.required_engines
    assert "F04" in plan.required_engines
    assert "FI01" in plan.required_engines
    assert "X03" in plan.required_engines
    assert "R01" in plan.required_engines

    # 5. Execute Full Multi-Modal Case Analysis DAG
    results = await execute_case_analysis_plan(db, test_case)

    assert results["case_id"] == "case_multimodal_001"
    assert results["successful_engines"] > 0
    assert results["failed_engines"] == 0
    assert results["observations_created"] > 0

    # 6. Verify Actual Engine Outputs & Provenance
    telemetry = results["telemetry"]
    tel_map = {t["engine_id"]: t for t in telemetry}

    # E01 Integrity & Metadata
    e01_out = tel_map["E01"]["outputs"][0]
    assert e01_out["file_size_bytes"] > 0
    assert e01_out["file_accessible"] is True

    # F04 Damage Engine correctly extracted pry damage from JPG
    f04_rec = tel_map.get("F04")
    assert f04_rec is not None
    assert f04_rec["outputs"][0]["damage_category"] == "MECHANICAL_PRY_DEFORMATION"

    # FI02 Reconciled Shrinkage from CSV inventory
    fi02_rec = tel_map.get("FI02")
    assert fi02_rec is not None
    assert fi02_rec["outputs"][0]["total_missing_units"] == 3
    assert fi02_rec["outputs"][0]["total_shrinkage_usd"] == 749.97

    # X03 Correlated CCTV presence with Financial Deficit
    x03_rec = tel_map.get("X03")
    assert x03_rec is not None
    assert x03_rec["outputs"][0]["correlation_strength"] >= 0.85

    # R01 Hypothesis generation: if LLM is available, must have ≥ 4 citations.
    # If LLM is quota-exceeded / unavailable, R01 must be BLOCKED (not produce synthetic output).
    r01_rec = tel_map.get("R01")
    assert r01_rec is not None
    if r01_rec["status"] in ["BLOCKED", "PARTIAL"]:
        # Correct: LLM unavailable → BLOCKED, no synthetic hypotheses.
        # Check that failure_reason explains the block
        assert r01_rec.get("failure_reason") is not None or (
            r01_rec.get("outputs") and r01_rec["outputs"][0].get("hypothesis_category") in [
                "INSUFFICIENT_EVIDENCE", "PARTIAL_CIRCUMSTANTIAL"
            ]
        ), f"BLOCKED R01 must have failure_reason or INSUFFICIENT_EVIDENCE output, got: {r01_rec}"
    else:
        # LLM was available: validate citation quality
        assert r01_rec["outputs"], "R01 SUCCESS must have outputs"
        assert len(r01_rec["outputs"][0].get("supporting_evidence_citations", [])) >= 4, (
            f"R01 with LLM must produce ≥ 4 citations, got: {r01_rec['outputs'][0].get('supporting_evidence_citations')}"
        )
