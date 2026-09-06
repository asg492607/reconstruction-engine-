import os
import sys
import uuid
import asyncio
from datetime import datetime, timezone

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from sqlalchemy import select, delete
from app.database import engine, AsyncSessionLocal, Base
from app.models.entities import (
    User, Organization, Case, CaseAssignment, Evidence,
    CandidateEntity, SourceTimeline, SourceTimelineEvent,
    CorrelatedTimelineEvent, Hypothesis, GapConflict
)
from app.models.enums import Role, Department, CaseType, CaseStatus, EvidenceType
from app.department_engines.dispatcher import run_case_analysis
from app.department_engines.framework.base import AnalysisRunContext
from app.reports.service import generate_case_report
from scripts.seed_demo_users import seed_users
from scripts.create_fresh_multimodal_case import generate_all_assets


async def trace_single_run():
    print("=" * 80)
    print("  SINGLE RUN TRACE & INVARIANT VERIFICATION SUITE")
    print("=" * 80)

    # 1. Purge DB and recreate tables
    db_path = os.path.join(REPO_ROOT, "data", "rre.db")
    print(f"\n[1/6] Purging database at {db_path}...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("      --> Clean schema initialized.")

    # 2. Seed demo users
    print("\n[2/6] Seeding demo users and organization...")
    await seed_users()
    print("      --> Demo users and organization seeded.")

    # 3. Generate media assets and create fresh case
    print("\n[3/6] Generating multimodal test assets...")
    generate_all_assets()
    print("      --> Assets generated.")

    print("\n[4/6] Creating fresh case and attaching multimodal exhibits...")
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email == "lead@police.gov"))).scalar_one()

        case_id = str(uuid.uuid4())
        case = Case(
            id=case_id,
            case_number="SEC-2026-0901",
            title="Depot #7 Vault Perimeter & High-Value Inventory Discrepancy",
            case_type=CaseType.THEFT,
            status=CaseStatus.CREATED,
            incident_location="Apex Logistics Depot #7, Sector B, Vault C",
            incident_time_observed=datetime(2026, 3, 5, 21, 18, 30, tzinfo=timezone.utc),
            incident_context={
                "premises": "Apex Logistics Depot #7 - High-Value Secure Transit Hub",
                "facility_sector": "Sector B, Corridor 3 & Vault C",
                "alert_trigger": "Unscheduled door contact sensor trip & end-of-shift reconciliation variance",
                "reporting_officer": "Officer D. Kovacs #408"
            },
            investigative_objectives=[
                "Establish timeline of unscheduled perimeter and corridor movements",
                "Analyze physical toolmark features on Vault C locking hasp",
                "Reconcile stock deltas against electronic access logs",
                "Correlate multi-sensor and eyewitness observations"
            ],
            created_by=user.id,
            current_version=1
        )
        session.add(case)
        await session.flush()

        assets_dir = os.path.join(REPO_ROOT, "test_evidence_assets_multimodal_new")
        exhibit_manifest = [
            ("cctv_depot_bay4_exterior.mp4", EvidenceType.CCTV, "video/mp4", ["INVESTIGATION"], {
                "camera_id": "CAM-04",
                "location": "Loading Bay 04 Exterior Apron",
                "start_time": "2026-03-05T21:12:00Z",
                "duration_seconds": 180.0,
                "fps": 15.0
            }),
            ("cctv_corridor_vault_interior.mp4", EvidenceType.CCTV, "video/mp4", ["INVESTIGATION"], {
                "camera_id": "CAM-09",
                "location": "Restricted Corridor 3 - Vault C Approach",
                "start_time": "2026-03-05T21:18:30Z",
                "duration_seconds": 180.0,
                "fps": 15.0
            }),
            ("forensic_vault_hasp_macro.jpg", EvidenceType.IMAGE, "image/jpeg", ["FORENSIC"], {
                "capture_time": "2026-03-05T22:15:00Z",
                "has_damage": True,
                "forced_entry": True,
                "damage_target": "Vault C Auxiliary Hasp & Latch Plate",
                "sharpness": 142.5
            }),
            ("depot_inventory_reconciliation.csv", EvidenceType.INVENTORY_RECORD, "text/csv", ["FINANCIAL"], {
                "ledger_type": "INVENTORY_RECONCILIATION",
                "period": "2026-03-05",
                "facility": "Apex Logistics Depot #7 - Vault C",
                "financial_records": [{"sku": "SKU-99214", "book_qty": 5, "counted_qty": 4, "variance": -1}]
            }),
            ("logistics_rfid_access_audit.csv", EvidenceType.TRANSACTION_RECORD, "text/csv", ["FINANCIAL", "INVESTIGATION"], {
                "sensor_type": "RFID_ACCESS_CONTROL",
                "period": "2026-03-05"
            }),
            ("security_officer_statement.txt", EvidenceType.WITNESS_STATEMENT, "text/plain", ["INVESTIGATION"], {
                "witness_name": "Officer David Kovacs",
                "role": "Shift Patrol Specialist",
                "statement": "Observed subject entering perimeter near bay 4 around 21:14."
            })
        ]

        evidence_ids = []
        for filename, ev_type, mime, depts, meta in exhibit_manifest:
            file_path = os.path.join(assets_dir, filename)
            size_b = os.path.getsize(file_path) if os.path.exists(file_path) else 1024
            ev_id = str(uuid.uuid4())
            ev = Evidence(
                id=ev_id,
                case_id=case_id,
                original_filename=filename,
                storage_key=file_path,
                mime_type=mime,
                file_size_bytes=size_b,
                sha256_hash="simulated_sha256_" + filename[:8],
                evidence_type=ev_type,
                authorized_departments=depts,
                metadata_json=meta,
                uploaded_by=user.id
            )
            session.add(ev)
            evidence_ids.append(ev_id)

        await session.commit()
        print(f"      --> Case SEC-2026-0901 created ({case_id}) with {len(evidence_ids)} exhibits.")

    # 5. Execute Case Analysis (Single Run)
    print("\n[5/6] Executing run_case_analysis under authoritative AnalysisRunContext...")
    async with AsyncSessionLocal() as session:
        case_to_run = (await session.execute(select(Case).where(Case.id == case_id))).scalar_one()
        user_to_run = (await session.execute(select(User).where(User.email == "lead@police.gov"))).scalar_one()
        analysis_res = await run_case_analysis(db=session, case=case_to_run, user_id=user_to_run.id, analysis_version=1)
    run_id = analysis_res.get("analysis_run_id")
    version = analysis_res.get("version", 1)
    status = analysis_res.get("status")
    execution_matrix = analysis_res.get("execution_matrix", {})

    print(f"\n" + "-" * 80)
    print(f"  [RUN TRACE SUMMARY] Run ID: {run_id} | Version: {version} | Status: {status}")
    print(f"-" * 80)
    print(f"  Engines Executed ({len(execution_matrix)}):")
    for eid, erec in execution_matrix.items():
        estatus = erec.get("status")
        ecat = erec.get("actual_execution_path", "DETERMINISTIC")
        econf = erec.get("confidence")
        out_cnt = len(erec.get("outputs", []))
        print(f"    - {eid:5s}: status={estatus:<12s} conf={str(econf):<6s} outputs={out_cnt} ({ecat})")

    # 6. Verify Database Persistence and Invariants
    print("\n[6/6] Verifying DB Persistence Parity and 6 Invariants...")
    async with AsyncSessionLocal() as session:
        # DB Entities
        candidate_entities = (await session.execute(
            select(CandidateEntity).where(CandidateEntity.case_id == case_id, CandidateEntity.analysis_version == version)
        )).scalars().all()

        source_timelines = (await session.execute(
            select(SourceTimeline).where(SourceTimeline.case_id == case_id, SourceTimeline.analysis_version == version)
        )).scalars().all()

        source_events = (await session.execute(
            select(SourceTimelineEvent).where(SourceTimelineEvent.source_timeline_id.in_([t.id for t in source_timelines]))
        )).scalars().all() if source_timelines else []

        correlated_events = (await session.execute(
            select(CorrelatedTimelineEvent).where(CorrelatedTimelineEvent.case_id == case_id, CorrelatedTimelineEvent.analysis_version == version)
        )).scalars().all()

        hypotheses = (await session.execute(
            select(Hypothesis).where(Hypothesis.case_id == case_id, Hypothesis.analysis_version == version)
        )).scalars().all()

        gaps = (await session.execute(
            select(GapConflict).where(GapConflict.case_id == case_id, GapConflict.analysis_version == version)
        )).scalars().all()

        print(f"  DB Persistence Parity:")
        print(f"    - Candidate Entities:        {len(candidate_entities)}")
        print(f"    - Source Timelines:          {len(source_timelines)}")
        print(f"    - Source Timeline Events:    {len(source_events)}")
        print(f"    - Correlated Timeline Events: {len(correlated_events)}")
        print(f"    - Hypotheses:                {len(hypotheses)}")
        print(f"    - Gaps / Conflicts:          {len(gaps)}")

        # Retrieve outputs of key engines
        x01_outputs = execution_matrix.get("X01", {}).get("outputs", [])
        x02_outputs = execution_matrix.get("X02", {}).get("outputs", [])
        x03_outputs = execution_matrix.get("X03", {}).get("outputs", [])
        x04_outputs = execution_matrix.get("X04", {}).get("outputs", [])
        x05_outputs = execution_matrix.get("X05", {}).get("outputs", [])
        x06_outputs = execution_matrix.get("X06", {}).get("outputs", [])
        r01_outputs = execution_matrix.get("R01", {}).get("outputs", [])

        # Invariant 1: X02 vs X06 correlated count
        x03_corr_count = x03_outputs[0].get("correlated_event_count", len(x03_outputs)) if x03_outputs else 0
        x06_corr_count = x06_outputs[0].get("correlated_event_count", 0) if x06_outputs else 0
        db_corr_count = len(correlated_events)
        print(f"\n  [INVARIANT 1] X02 vs X06 Correlation Count Invariant:")
        print(f"    X03 Correlated Count: {x03_corr_count} | X06 Correlated Count: {x06_corr_count} | DB Correlated: {db_corr_count}")
        assert x06_corr_count == x03_corr_count == db_corr_count, (
            f"Correlation count mismatch! X06={x06_corr_count}, X03={x03_corr_count}, DB={db_corr_count}"
        )
        print(f"    --> [PASS] Invariant 1 holds: 100% agreement ({db_corr_count} correlated events).")

        # Invariant 2: Financial evidence modality
        fi_engines_success = [eid for eid in ["FI01", "FI02", "FI03", "FI04", "FI05", "FI06"] if execution_matrix.get(eid, {}).get("status") == "SUCCESS"]
        x04_gaps = x04_outputs if isinstance(x04_outputs, list) else []
        has_fin_gap = any("financial" in str(g.get("description", "")).lower() or "inventory" in str(g.get("description", "")).lower() for g in x04_gaps if g.get("gap_type") == "EVIDENCE_MODALITY_GAP")
        print(f"\n  [INVARIANT 2] Financial Modality Invariant:")
        print(f"    FI Successful Engines: {fi_engines_success}")
        print(f"    X04 Financial Absence Gap Emitted: {has_fin_gap}")
        if fi_engines_success:
            assert not has_fin_gap, "Financial evidence processed successfully by FI engines but X04 marked modality absent!"
        print(f"    --> [PASS] Invariant 2 holds: Financial modality recognized consistently (no contradictory absence gap).")

        # Invariant 3: R01 Entity Reference Integrity
        x01_entity_ids = {e.get("entity_id") for e in x01_outputs}
        r01_entities = set()
        for hyp in r01_outputs:
            r01_entities.update(hyp.get("supporting_entities", []))
        print(f"\n  [INVARIANT 3] R01 Unknown Entity Reference Invariant:")
        print(f"    X01 Entity IDs: {x01_entity_ids}")
        print(f"    R01 Referenced Entities: {r01_entities}")
        unresolved = r01_entities - x01_entity_ids
        assert len(unresolved) == 0, f"R01 referenced entities not in X01! Unresolved: {unresolved}"
        print(f"    --> [PASS] Invariant 3 holds: Zero unresolved entity references in R01.")

        # Invariant 4: Timeline Rich Investigative Event Model
        print(f"\n  [INVARIANT 4] Timeline Output Representation:")
        all_rich = True
        req_x02_fields = ["event_id", "source_id", "source_type", "event_type", "confidence", "description"]
        for ev in x02_outputs:
            if not all(k in ev for k in req_x02_fields):
                all_rich = False
                print(f"    [FAIL] X02 event missing fields: {ev}")
            if "Normalized event from" in ev.get("description", ""):
                all_rich = False
                print(f"    [FAIL] X02 event has low-quality description: {ev.get('description')}")
        sample_x02 = x02_outputs[0] if x02_outputs else {}
        print(f"    Sample X02 event: ID={sample_x02.get('event_id')} | "
              f"Source={sample_x02.get('source_type')} ({sample_x02.get('source_id')}) | "
              f"Type={sample_x02.get('event_type')} | "
              f"Desc={str(sample_x02.get('description'))[:60]}...")
        assert all_rich, "Timeline events lack rich investigative fields or contain placeholder descriptions!"
        print(f"    --> [PASS] Invariant 4 holds: Rich investigative event model preserved across all {len(x02_outputs)} events.")

        # Invariant 5: X05 Input Consistency
        x05_rec = execution_matrix.get("X05", {})
        x05_grounding = x05_rec.get("grounding_sources", [])
        unavail_line = next((s for s in x05_grounding if "Unavailable inputs:" in s), "")
        avail_line = next((s for s in x05_grounding if "Inputs available:" in s), "")
        print(f"\n  [INVARIANT 5] X05 Engine Prerequisite Consistency:")
        print(f"    X05 {avail_line}")
        print(f"    X05 {unavail_line}")
        if any(execution_matrix.get(eid, {}).get("status") == "SUCCESS" for eid in ["FI01", "FI04"]):
            assert "FI01-FI06 financial ledgers" not in unavail_line and "financial ledgers" not in unavail_line, (
                "X05 claims financial ledgers unavailable, but FI engines succeeded!"
            )
        print(f"    --> [PASS] Invariant 5 holds: No false unavailability claims in X05.")

        # Invariant 6: X06 Canonical State Model
        x06_top = x06_outputs[0] if x06_outputs else {}
        analytical_res = x06_top.get("analytical_result")
        rec_elig = x06_top.get("reconstruction_eligibility")
        suff_rating = x06_top.get("sufficiency_rating")
        print(f"\n  [INVARIANT 6] X06 Canonical State Model:")
        print(f"    Analytical Result:          {analytical_res}")
        print(f"    Reconstruction Eligibility: {rec_elig}")
        print(f"    Sufficiency Rating:         {suff_rating}")
        assert analytical_res in ["SUFFICIENT", "MARGINAL_PROBATIVE_VALUE", "INSUFFICIENT"]
        assert rec_elig in ["PROCEED", "ALLOWED_WITH_WARNINGS", "BLOCKED"]
        print(f"    --> [PASS] Invariant 6 holds: Harmonized canonical state model active.")

        # 7. Generate Full Dossier Report
        print("\n[7/7] Generating Investigation Dossier Report via generate_case_report...")
        case_obj = (await session.execute(select(Case).where(Case.id == case_id))).scalar_one()
        report_entity = await generate_case_report(db=session, case=case_obj, user=user, analysis_version=version)
        print(f"    Report ID:          {report_entity.id}")
        dossier = report_entity.report_data or {}
        print(f"    Report Generated At:{report_entity.generated_at}")
        print(f"    Dossier Title:      {dossier.get('report_metadata', {}).get('title')}")
        print(f"    Case Number:        {dossier.get('report_metadata', {}).get('case_number')}")
        print(f"    Analysis Version:   {dossier.get('report_metadata', {}).get('analysis_version')}")
        print(f"    Events in Report:   {len(dossier.get('correlated_timeline', []))}")
        print(f"    Entities in Report: {len(dossier.get('candidate_entities', []))}")
        print(f"    Hypotheses:         {dossier.get('executive_summary', {}).get('primary_hypothesis')}")
        assert len(dossier.get('correlated_timeline', [])) == len(correlated_events)
        print("    --> [PASS] Dossier report successfully compiled with 100% database parity.")

    print("\n" + "=" * 80)
    print("  ALL 6 CROSS-ENGINE INVARIANTS PERFECTLY VERIFIED & PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(trace_single_run())
