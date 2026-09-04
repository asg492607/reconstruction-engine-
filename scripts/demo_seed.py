import asyncio
import io
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal, engine, Base
from app.auth.service import get_or_create_organization, create_user, get_user_by_email
from app.auth.schemas import UserRegister
from app.cases.service import create_case, get_case_by_id
from app.cases.schemas import CaseCreate
from app.models.enums import Role, Department, EvidenceType, CaseType
from app.evidence.service import ingest_evidence
from app.department_engines.dispatcher import dispatch_evidence_processing
from app.entities.service import auto_link_case_observations, confirm_entity_link, list_candidate_entities
from app.timelines.correlator import correlate_case_timelines
from app.reconstruction.engine import generate_theft_hypotheses, review_hypothesis
from app.reports.service import generate_case_report
from fastapi import UploadFile

DEMO_EVIDENCE = [
    ("cctv_entrance.mp4", b"CCTV_VIDEO_FRAME_ENTRANCE_SUBJECT_T1_ENTER", "video/mp4", EvidenceType.CCTV),
    ("cctv_aisle.mp4", b"CCTV_VIDEO_FRAME_AISLE_DISPLAY_SUBJECT_T1_LOITER", "video/mp4", EvidenceType.CCTV),
    ("cctv_exit.mp4", b"CCTV_VIDEO_FRAME_EXIT_TURNSTILE_SUBJECT_T1_LEAVE", "video/mp4", EvidenceType.CCTV),
    ("witness_statement.txt", b"I saw a person in a black jacket near the electronics shelf around 8:40 PM.", "text/plain", EvidenceType.WITNESS_STATEMENT),
    ("inventory_log.csv", b"item,serial,status,delta,last_verified,reported_missing\niPhone 15 Pro,SN-88219,MISSING,-1,2026-01-15T20:30:00Z,2026-01-15T21:00:00Z\n", "text/csv", EvidenceType.INVENTORY_RECORD),
    ("transactions.csv", b"transaction_id,timestamp,item,amount\nTX-1001,2026-01-15T20:35:00Z,Screen Guard,499\n", "text/csv", EvidenceType.TRANSACTION_RECORD),
    ("vehicle_sighting.txt", b"Dark SUV seen outside at 8:48 PM, partial plate noted: MH12-AB-9821.", "text/plain", EvidenceType.VEHICLE_RECORD),
    ("crime_scene_shelf.jpg", b"EXIF_IMAGE_SEVERED_SECURITY_TETHER", "image/jpeg", EvidenceType.IMAGE)
]

async def seed_demo_case():
    print("==================================================================")
    print("  REALITY RECONSTRUCTION ENGINE (RRE) — DEMO CASE SEEDER")
    print("==================================================================")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        # 1. Create or fetch demo users for all roles
        demo_accounts = [
            ("lead@police.gov", "password123", "Lead Detective Harris", Role.LEAD_INVESTIGATOR, Department.INVESTIGATION),
            ("forensic@police.gov", "password123", "Dr. Aris Thorne", Role.FORENSIC_OFFICER, Department.FORENSIC),
            ("financial@police.gov", "password123", "Auditor Claire Sterling", Role.FINANCIAL_ANALYST, Department.FINANCIAL),
            ("judge@justice.gov", "password123", "Magistrate Patricia Vance", Role.PROSECUTOR_JUDGE, Department.LEGAL),
            ("admin@police.gov", "password123", "System Administrator", Role.ADMIN, Department.ADMIN),
            ("investigator.roy@police.gov", "InvestigatorPass2026!", "Detective Roy (Lead)", Role.LEAD_INVESTIGATOR, Department.INVESTIGATION),
        ]

        user = None
        for email, pwd, name, role, dept in demo_accounts:
            existing = await get_user_by_email(db, email)
            if not existing:
                print(f"[+] Creating User: {name} ({email})...")
                created = await create_user(
                    db,
                    UserRegister(
                        email=email,
                        password=pwd,
                        full_name=name,
                        role=role,
                        department=dept,
                        organization_name="Metropolitan Police Department"
                    )
                )
                if email == "lead@police.gov":
                    user = created
            elif email == "lead@police.gov":
                user = existing
        
        if not user:
            user = await get_user_by_email(db, "lead@police.gov")

        # 2. Create the Theft Case
        print("[+] Creating Case: Grand Electronics iPhone 15 Pro Theft...")
        case = await create_case(
            db,
            CaseCreate(
                title="Grand Electronics Showroom iPhone 15 Pro Theft",
                case_type=CaseType.THEFT,
                incident_location="Grand Electronics, Sector 18, Central Mall",
                incident_time_observed=datetime(2026, 1, 15, 20, 45, 0, tzinfo=timezone.utc),
                incident_time_estimated={"min": "2026-01-15T20:30:00Z", "max": "2026-01-15T21:00:00Z"}
            ),
            user=user
        )
        print(f"    Case Created: {case.case_number} (ID: {case.id})")

        # 3. Ingest and Process Evidence
        print("[+] Ingesting and Processing 8 heterogeneous evidence files...")
        for filename, content, mime, ev_type in DEMO_EVIDENCE:
            mock_file = UploadFile(
                filename=filename,
                file=io.BytesIO(content),
                headers={"content-type": mime}
            )
            ev = await ingest_evidence(
                db=db,
                case_id=case.id,
                user=user,
                upload_file=mock_file,
                evidence_type=ev_type
            )
            obs = await dispatch_evidence_processing(db, case, ev)
            print(f"    - {filename} ({ev.evidence_type.value}) -> SHA256: {ev.sha256_hash[:12]}... -> {len(obs)} observations")

        # 4. Auto-link Candidate Entities & Confirm P1 Link
        print("[+] Running Candidate Entity Linker...")
        links = await auto_link_case_observations(db, case.id)
        print(f"    Generated {len(links)} probabilistic candidate entity links.")
        if links:
            # Human confirmation
            confirmed = await confirm_entity_link(db, case.id, links[0].id, user, "Confirmed against CCTV-01 entrance visual profile.")
            print(f"    Human Investigator confirmed link for Candidate Entity: P1 (Confidence: {confirmed.link_confidence * 100:.1f}%)")

        # 5. Timeline Correlation & Gap Detection
        print("[+] Correlating Source Timelines into authoritative Chronology...")
        corr_events = await correlate_case_timelines(db, case)
        print(f"    Correlated {len(corr_events)} unified timeline events across cameras, statements, and inventory.")

        # 6. Generate Theft Hypotheses & Two-Layer Self-Challenge
        print("[+] Executing Evidence-Constrained Reconstruction Engine...")
        hypotheses = await generate_theft_hypotheses(db, case)
        for h in hypotheses:
            print(f"    * {h.label} [Strength: {h.overall_strength.value}]")
            print(f"      - Layer 1 Deterministic Issues: {len(h.deterministic_issues)}")
            print(f"      - Layer 2 AI Counterpoints: {len(h.ai_challenge_notes)}")

        # 7. Generate Official Case Report
        print("[+] Synthesizing Final Case Report with Judicial AI Disclosure...")
        report = await generate_case_report(db, case, user)
        print(f"    Report Version {report.version} generated successfully (ID: {report.id})")

    print("==================================================================")
    print("  SEEDING COMPLETE! Start server with:")
    print("  .venv\\Scripts\\uvicorn app.main:app --reload --port 8000")
    print("  API Documentation: http://localhost:8000/docs")
    print("  Interactive Web UI: http://localhost:8000/")
    print("==================================================================")

if __name__ == "__main__":
    asyncio.run(seed_demo_case())
