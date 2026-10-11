"""
Reality Reconstruction Engine (RRE 2.0)
========================================
Presentation Showcase Case Generator & Turnkey Pipeline Runner
Case: SEC-2026-SHOWCASE (Apex Logistics Depot #7 - Vault C Heist)

This standalone runner:
1. Generates authentic multimodal assets into testing/inputs/
2. Seeds presentation credentials & organizations into the database
3. Preserves and registers exhibits with SHA-256 cryptographic integrity
4. Executes the full analytical engine pipeline (Correlations, Entities, Hypotheses, Gaps/Conflicts)
5. Pre-compiles the official investigative dossier report for 1-click presentation demo
"""

import os
import sys
import uuid
import asyncio
from datetime import datetime, timezone
import cv2
import numpy as np
from PIL import Image, ImageDraw

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

INPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inputs")
os.makedirs(INPUTS_DIR, exist_ok=True)


# ============================================================================
# 1. INPUT GENERATION: 9 MULTIMODAL EVIDENCE EXHIBITS
# ============================================================================

def generate_cctv_video(filename: str, cam_name: str, base_time_str: str, scenario: str):
    """Generates a realistic surveillance video with camera HUD, timestamp OSD, and bounding boxes."""
    filepath = os.path.join(INPUTS_DIR, filename)
    width, height = 640, 480
    fps = 15.0
    num_frames = 60  # 4.0 seconds

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

    for frame_idx in range(num_frames):
        frame = np.full((height, width, 3), 32, dtype=np.uint8)

        # Draw architectural warehouse grid & floor perspective
        for y in range(200, height, 30):
            cv2.line(frame, (0, y), (width, y), (48, 48, 52), 1)
        for x in range(0, width, 45):
            cv2.line(frame, (x, 200), (int(x * 1.3 - 60), height), (48, 48, 52), 1)

        if scenario == "BAY_04":
            # Exterior loading dock apron & roll-up shutter
            cv2.rectangle(frame, (130, 70), (510, 420), (70, 70, 75), 2)
            cv2.putText(frame, "LOADING BAY 04 - EXTERIOR LOGISTICS APRON", (140, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (140, 140, 140), 1)
            # Inbound subject with shoulder gear
            x_pos = int(170 + frame_idx * 3.5)
            cv2.rectangle(frame, (x_pos, 150), (x_pos + 80, 390), (0, 255, 0), 2)
            cv2.putText(frame, "TRACK_01 [BAY_INBOUND_SUBJECT]", (x_pos - 15, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 0), 1)
        elif scenario == "VAULT_C":
            # Restricted corridor & Vault C reinforced entrance
            cv2.rectangle(frame, (210, 90), (430, 430), (85, 85, 90), -1)
            cv2.rectangle(frame, (230, 110), (410, 430), (55, 55, 60), 2)
            cv2.putText(frame, "RESTRICTED VAULT C - HIGH VALUE REPOSITORY", (125, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 175), 1)
            # Subject approaching vault locking hasp
            x_pos = int(160 + frame_idx * 2.2)
            cv2.rectangle(frame, (x_pos, 140), (x_pos + 85, 395), (0, 165, 255), 2)
            cv2.putText(frame, "PROXIMITY_ALERT [VAULT_C_BREACH]", (x_pos - 20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 165, 255), 1)
        else: # GATE_12
            # Perimeter fence & North Gate 12 turnstile
            cv2.rectangle(frame, (90, 70), (550, 440), (65, 65, 70), 2)
            cv2.line(frame, (110, 380), (530, 380), (0, 0, 255), 2)
            cv2.putText(frame, "NORTH PERIMETER TURNSTILE - GATE 12", (135, 410), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 220), 1)
            # Subject rapid egress
            x_pos = int(230 + frame_idx * 4.2)
            cv2.rectangle(frame, (x_pos, 125), (x_pos + 85, 375), (0, 255, 0), 2)
            cv2.putText(frame, "OUTBOUND_EGRESS [PERIMETER_EXIT]", (x_pos - 15, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 0), 1)

        # Top On-Screen Display (OSD) status bar
        cv2.rectangle(frame, (0, 0), (width, 32), (0, 0, 0), -1)
        sec = frame_idx // 15
        ms = (frame_idx % 15) * 66
        current_time_str = f"{base_time_str}:{sec:02d}.{ms:03d} UTC"
        cv2.putText(frame, f"REC [LIVE]  {cam_name}  {current_time_str}", (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        cv2.circle(frame, (615, 16), 5, (0, 0, 255), -1)

        out.write(frame)

    out.release()
    print(f"  [+] Generated Video : {filename} ({os.path.getsize(filepath):,} bytes)")


def generate_macro_scene_image(filename: str):
    """Generates a high-resolution forensic crime scene photograph with NIST 10cm metric scale and EXIF tags."""
    filepath = os.path.join(INPUTS_DIR, filename)
    img = Image.new("RGB", (1200, 900), color=(38, 40, 44))
    draw = ImageDraw.Draw(img)

    # Steel door surface texture
    draw.rectangle([80, 140, 1120, 760], fill=(62, 65, 72), outline=(95, 100, 110), width=3)

    # Vault C Auxiliary Hasp & Latch Plate
    draw.rectangle([440, 280, 760, 620], fill=(28, 30, 34), outline=(150, 155, 165), width=4)
    draw.text((460, 305), "VAULT C AUXILIARY LOCKING HASP", fill=(210, 215, 225))

    # Mechanical pry striations (17.5mm bevel width)
    draw.line([550, 420, 650, 490], fill=(230, 230, 240), width=6)
    draw.line([540, 430, 640, 500], fill=(190, 190, 205), width=4)
    draw.ellipse([525, 400, 675, 515], outline=(255, 50, 50), width=3)
    draw.text((465, 535), "MECHANICAL PRY STRIATION (17.5mm BEVEL WIDTH)", fill=(255, 120, 120))

    # NIST Calibrated 10cm Metric Scale
    draw.rectangle([780, 660, 1070, 715], fill=(255, 235, 50), outline=(0, 0, 0), width=2)
    draw.text((800, 675), "NIST CALIBRATED 10CM SCALE (1DIV = 10MM)", fill=(0, 0, 0))
    for tick in range(780, 1070, 14):
        draw.line([tick, 695, tick, 715], fill=(0, 0, 0), width=1)

    # Forensic Evidence Header Banner
    draw.rectangle([0, 0, 1200, 50], fill=(16, 18, 22))
    draw.text((25, 16), "FORENSIC IDENTIFICATION SECTION - SCENE EXHIBIT #F-01", fill=(215, 230, 255))
    draw.text((930, 16), "2026-03-05 22:15:00 UTC", fill=(175, 180, 190))

    # Real Forensic EXIF metadata
    exif = img.getexif()
    exif[0x010F] = "Nikon"
    exif[0x0110] = "D850 Forensic Macro"
    exif[0x9003] = "2026:03:05 22:15:00"
    exif[0x9004] = "2026:03:05 22:15:00"

    img.save(filepath, "JPEG", quality=95, exif=exif)
    print(f"  [+] Generated Photo : {filename} ({os.path.getsize(filepath):,} bytes)")


def generate_latent_fingerprint(filename: str):
    """Generates an authentic latent fingerprint friction ridge card with calibrated millimeter scale."""
    filepath = os.path.join(INPUTS_DIR, filename)
    img = Image.new("L", (720, 720), color=238)
    draw = ImageDraw.Draw(img)

    # Synthetic friction ridge patterns
    cx, cy = 360, 380
    for r in range(16, 230, 7):
        bbox = [cx - r, cy - int(r * 1.22), cx + r, cy + int(r * 1.22)]
        draw.arc(bbox, start=25, end=155, fill=30, width=2)
        draw.arc(bbox, start=205, end=335, fill=40, width=2)

    # Door handle contact smudge distortion
    draw.rectangle([270, 330, 450, 400], fill=175)
    for i in range(28):
        draw.line([290 + i * 5, 330, 300 + i * 5, 400], fill=65, width=1)

    # Forensic card border & scale
    draw.rectangle([25, 25, 695, 695], outline=0, width=2)
    draw.text((45, 45), "LATENT FRICTION RIDGE CARD - LIFTED FROM VAULT C EXTERIOR HANDLE", fill=0)
    draw.text((45, 70), "CASE REF: SEC-2026-SHOWCASE  |  EXAMINER: D. CHEN, CLPE", fill=50)
    draw.rectangle([45, 630, 385, 668], fill=255, outline=0, width=2)
    draw.text((60, 642), "CALIBRATED METRIC SCALE: 1CM = 50PX", fill=0)

    img.save(filepath, "PNG")
    print(f"  [+] Generated Print : {filename} ({os.path.getsize(filepath):,} bytes)")


def generate_rfid_access_csv(filename: str):
    """Generates an electronic RFID access control CSV ledger showing audit events and unscheduled alarm."""
    filepath = os.path.join(INPUTS_DIR, filename)
    csv_data = """timestamp,terminal_id,badge_id,event_type,location,status
2026-03-05T21:05:12Z,TERM-EXT-01,BADGE-8841,BADGE_SCAN_GRANTED,Exterior Pedestrian Turnstile,AUTHORIZED
2026-03-05T21:11:45Z,TERM-BAY-04,BADGE-9912,VEHICLE_GATE_HOLD,Bay 4 Logistics Apron,AUTHORIZED
2026-03-05T21:18:22Z,TERM-VLT-C,BADGE-UNKNOWN,SENSOR_CONTACT_TRIPPED,Vault C Corridor Boundary,UNSCHEDULED_ALARM
2026-03-05T21:19:05Z,TERM-VLT-C,BADGE-UNKNOWN,DOOR_FORCED_OPEN_SIGNAL,Vault C Auxiliary Latch,TAMPER_ALARM
2026-03-05T21:25:50Z,TERM-EXT-02,BADGE-7104,BADGE_SCAN_GRANTED,North Perimeter Gate 12,AUTHORIZED
2026-03-05T21:32:10Z,TERM-SEC-01,BADGE-3001,PATROL_CHECK_LOGGED,Central Security Monitoring,AUTHORIZED
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(csv_data)
    print(f"  [+] Generated Access: {filename} ({os.path.getsize(filepath):,} bytes)")


def generate_inventory_reconciliation_csv(filename: str):
    """Generates an inventory stock ledger demonstrating a $37,000 physical deficit in high-value catalyst assets."""
    filepath = os.path.join(INPUTS_DIR, filename)
    csv_data = """sku,product_name,category,expected_stock_count,physical_count,unit_cost_usd,location_bin
SKU-OPT-100,100G Optical Transceiver Modules,TELECOM_HARDWARE,60,60,450.00,BIN-C-01
SKU-CAT-809,Industrial Platinum Catalyst Cylinders,PRECIOUS_MATERIALS,4,2,18500.00,BIN-C-VAULT-04
SKU-NVME-400,High-Density 32TB NVMe Server Drives,ENTERPRISE_STORAGE,24,24,890.00,BIN-C-02
SKU-SFP-28,25G SFP28 Direct Attach Copper Cable,CABLES_ACCESSORIES,150,150,35.00,BIN-C-03
SKU-PSU-1600,1600W Titanium Server Power Supply,POWER_INFRASTRUCTURE,18,18,320.00,BIN-C-05
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(csv_data)
    print(f"  [+] Generated Ledger: {filename} ({os.path.getsize(filepath):,} bytes)")


def generate_witness_statement_text(filename: str):
    """Generates a sworn witness deposition from the on-duty security officer."""
    filepath = os.path.join(INPUTS_DIR, filename)
    statement = """SECURITY OFFICER FIRSTHAND OBSERVATION REPORT
INCIDENT ID: SEC-2026-SHOWCASE
LOCATION: Apex Logistics Depot #7, Sector B
OFFICER: David Kovacs (Shift Patrol Specialist #408)
DATE OF INTERVIEW: 2026-03-05 22:30 UTC

STATEMENT:
"On the evening of March 5, 2026, I was assigned to interior patrol duty covering Sector B and the transit warehouse bays.
At approximately 21:18 UTC, the secondary annunciator panel in the sub-station alerted to an unscheduled contact trip on the Vault C boundary door.
I immediately moved on foot toward Corridor 3 to investigate the alert.
As I approached the intersection leading from the vault hallway, at roughly 21:22 UTC, I observed an individual wearing a dark grey hooded jacket and carrying a dark shoulder sling bag walking rapidly toward the north exit corridor.
The person did not stop or answer when I called out from down the hall and exited through the North Gate 12 turnstile area before I could intercept them.
Upon reaching Vault C at 21:24 UTC, I observed that the auxiliary padlock hasp was hanging open with visible fresh gouge marks on the latch plate.
I contacted Central Dispatch at 21:25 UTC to declare a physical perimeter breach and requested an immediate shift inventory audit."

I declare that this statement is an accurate and direct record of my sensory observations.
Signed: Officer David Kovacs, ID #408
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(statement)
    print(f"  [+] Generated Witness: {filename} ({os.path.getsize(filepath):,} bytes)")


def generate_forensic_metallurgical_report(filename: str):
    """Generates a laboratory metallurgical examination report on the prying implement toolmarks."""
    filepath = os.path.join(INPUTS_DIR, filename)
    report = """FORENSIC PHYSICAL EVIDENCE & TOOLMARK EXAMINATION
LABORATORY REPORT #FLR-2026-03-902
EXAMINATION DATE: 2026-03-05 23:15 UTC
AGENCY CASE: SEC-2026-SHOWCASE

EXHIBIT RECEIVED:
Exhibit F-01: Vault C door auxiliary steel locking hasp and mounting plate.

EXAMINATION & MACROSCOPIC ANALYSIS:
1. Microscopic inspection at 35x and 70x magnification reveals distinctive compressive shear and levering marks along the strike edge of the mounting plate.
2. Blade contact impression width measures 17.5 mm (+/- 0.2 mm) with a single-bevel profile and an impression depth of 4.5 mm.
3. Localized striations indicate unidirectional prying leverage applied from below the hasp body.
4. Trace copper-alloy microscopic transfer was detected along the primary striation furrow, indicating tool composition or plating.

EXAMINER OPINION:
The deformation is consistent with mechanical forced entry using a flat-blade prying implement (nominal blade width ~17.5mm, such as a heavy-duty pry lever or chisel). Toolmark features are suitable for microscopic class characteristic comparison if candidate physical tools are submitted.

Lead Forensic Examiner: Dr. Elena Rostova, D-ABC
Physical Evidence Unit
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  [+] Generated Lab Rpt: {filename} ({os.path.getsize(filepath):,} bytes)")


def generate_all_presentation_inputs():
    print("\n[PHASE 1/4] Generating Genuine Multimodal Presentation Evidence in testing/inputs/ ...")
    generate_cctv_video("1_cctv_bay04_inbound_arrival.mp4", "CAM-04 [BAY_04_EXTERIOR]", "2026-03-05 21:12", "BAY_04")
    generate_cctv_video("2_cctv_vault_c_approach_breach.mp4", "CAM-09 [VAULT_C_CORRIDOR]", "2026-03-05 21:18", "VAULT_C")
    generate_cctv_video("3_cctv_gate12_north_outbound.mp4", "CAM-12 [GATE_12_NORTH]", "2026-03-05 21:26", "GATE_12")
    generate_macro_scene_image("4_forensic_vault_hasp_photomacrography.jpg")
    generate_latent_fingerprint("5_forensic_latent_fingerprint_lift.png")
    generate_rfid_access_csv("6_rfid_access_control_audit.csv")
    generate_inventory_reconciliation_csv("7_depot_inventory_reconciliation.csv")
    generate_witness_statement_text("8_witness_officer_statement.txt")
    generate_forensic_metallurgical_report("9_metallurgical_laboratory_report.txt")
    print("      --> All 9 Multimodal Presentation Inputs successfully created.")


# ============================================================================
# 2. SEED DATABASE, REGISTER CASE & ATTACH EXHIBITS
# ============================================================================

async def setup_and_run_presentation_case():
    from app.database import engine, AsyncSessionLocal, Base
    from app.models.entities import (
        User, Organization, Case, CaseAssignment, Evidence,
        CandidateEntity, SourceTimeline, CorrelatedTimelineEvent,
        Hypothesis, GapConflict
    )
    from app.models.enums import CaseType, CaseStatus, EvidenceType, ProcessingStatus, Role, Department
    from app.evidence.storage import storage_manager
    from app.department_engines.dispatcher import run_case_analysis
    from app.reports.service import generate_case_report
    from scripts.seed_demo_users import seed_users
    from sqlalchemy import select

    print("\n[PHASE 2/4] Initializing Database Schema & Seeding Presentation Credentials ...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await seed_users()
    print("      --> Demo users verified: lead@police.gov, forensic@police.gov, financial@police.gov, legal@police.gov")

    print("\n[PHASE 3/4] Ingesting Case SEC-2026-SHOWCASE with Cryptographic Preservation ...")
    async with AsyncSessionLocal() as session:
        user_res = await session.execute(select(User).where(User.email == "lead@police.gov"))
        lead_user = user_res.scalar_one()

        # Check if case already exists
        existing_case = (await session.execute(
            select(Case).where(Case.case_number == "SEC-2026-SHOWCASE")
        )).scalar_one_or_none()

        if existing_case:
            case = existing_case
            print(f"      --> Existing Showcase Case found: {case.case_number} ({case.id})")
        else:
            case = Case(
                id=str(uuid.uuid4()),
                case_number="SEC-2026-SHOWCASE",
                title="Apex Logistics Depot #7: Vault C Forced Entry & High-Value Inventory Discrepancy",
                case_type=CaseType.THEFT,
                status=CaseStatus.RECONSTRUCTION,
                incident_location="Apex Logistics Depot #7, Sector B, Vault C",
                incident_time_observed=datetime(2026, 3, 5, 21, 18, 30, tzinfo=timezone.utc),
                incident_context={
                    "facility": "Apex Logistics High-Value Depot #7",
                    "sector": "Sector B, Corridor 3 & Vault C Security Enclosure",
                    "alert_trigger": "Unscheduled door contact sensor trip (21:18:22Z) & shift reconciliation variance",
                    "reporting_officer": "Officer David Kovacs #408",
                    "financial_loss": "$37,000 USD (2x Platinum Catalyst Cylinders SKU-CAT-809)"
                },
                investigative_objectives=[
                    "Establish chronological multi-sensor timeline from Bay 4 entry to North Gate 12 egress",
                    "Analyze physical toolmark features on Vault C locking hasp (17.5mm single-bevel striation)",
                    "Reconcile stock discrepancy against electronic RFID access logs ($37,000 inventory deficit)",
                    "Correlate candidate suspect entities across surveillance, latent print, and eyewitness testimony",
                    "Validate competing hypotheses under Deterministic (L1) and Adversarial AI (L2) scrutiny"
                ],
                created_by=lead_user.id,
                current_version=1
            )
            session.add(case)
            await session.commit()
            await session.refresh(case)
            print(f"      --> Created Showcase Case: {case.case_number} ({case.id})")

        # Assign all team members to this case
        all_users = (await session.execute(select(User))).scalars().all()
        for u in all_users:
            existing_assign = (await session.execute(
                select(CaseAssignment).where(CaseAssignment.case_id == case.id, CaseAssignment.user_id == u.id)
            )).scalar_one_or_none()
            if not existing_assign:
                session.add(CaseAssignment(
                    case_id=case.id,
                    user_id=u.id,
                    department=u.department,
                    assigned_by=lead_user.id
                ))
        await session.commit()

        # Exhibit Manifest
        exhibit_manifest = [
            ("1_cctv_bay04_inbound_arrival.mp4", EvidenceType.CCTV, "video/mp4", ["INVESTIGATION"], {
                "camera_id": "CAM-04",
                "location": "Loading Bay 04 Exterior Apron",
                "start_time": "2026-03-05T21:12:00Z",
                "duration_seconds": 180.0,
                "fps": 15.0
            }),
            ("2_cctv_vault_c_approach_breach.mp4", EvidenceType.CCTV, "video/mp4", ["INVESTIGATION"], {
                "camera_id": "CAM-09",
                "location": "Restricted Corridor 3 - Vault C Approach",
                "start_time": "2026-03-05T21:18:30Z",
                "duration_seconds": 180.0,
                "fps": 15.0
            }),
            ("3_cctv_gate12_north_outbound.mp4", EvidenceType.CCTV, "video/mp4", ["INVESTIGATION"], {
                "camera_id": "CAM-12",
                "location": "North Perimeter Turnstile Gate 12",
                "start_time": "2026-03-05T21:26:15Z",
                "duration_seconds": 180.0,
                "fps": 15.0
            }),
            ("4_forensic_vault_hasp_photomacrography.jpg", EvidenceType.IMAGE, "image/jpeg", ["FORENSIC"], {
                "capture_time": "2026-03-05T22:15:00Z",
                "camera_make": "Nikon",
                "camera_model": "D850 Forensic Macro",
                "has_damage": True,
                "forced_entry": True,
                "damage_target": "Vault C Auxiliary Hasp & Latch Plate",
                "sharpness": 142.5
            }),
            ("5_forensic_latent_fingerprint_lift.png", EvidenceType.IMAGE, "image/png", ["FORENSIC"], {
                "capture_time": "2026-03-05T22:45:00Z",
                "impression_target": "Vault C Exterior Handle",
                "latent_method": "Black Magnetic Powder Lift",
                "sharpness": 88.0
            }),
            ("6_rfid_access_control_audit.csv", EvidenceType.TRANSACTION_RECORD, "text/csv", ["FINANCIAL", "INVESTIGATION"], {
                "sensor_type": "RFID_ACCESS_CONTROL",
                "period": "2026-03-05"
            }),
            ("7_depot_inventory_reconciliation.csv", EvidenceType.INVENTORY_RECORD, "text/csv", ["FINANCIAL"], {
                "ledger_type": "INVENTORY_RECONCILIATION",
                "period": "2026-03-05",
                "facility": "Apex Logistics Depot #7 - Vault C",
                "financial_records": [{"sku": "SKU-CAT-809", "book_qty": 4, "counted_qty": 2, "variance": -2, "loss_usd": 37000.0}]
            }),
            ("8_witness_officer_statement.txt", EvidenceType.WITNESS_STATEMENT, "text/plain", ["INVESTIGATION"], {
                "witness_name": "Officer David Kovacs",
                "role": "Shift Patrol Specialist",
                "interview_time": "2026-03-05T22:30:00Z"
            }),
            ("9_metallurgical_laboratory_report.txt", EvidenceType.FORENSIC_REPORT, "text/plain", ["FORENSIC"], {
                "examiner": "Dr. Elena Rostova",
                "lab_reference": "FLR-2026-03-902",
                "date": "2026-03-05"
            })
        ]

        print("      --> Preserving exhibits into Evidence Vault (calculating SHA-256 digests):")
        for filename, ev_type, mime, depts, meta in exhibit_manifest:
            file_path = os.path.join(INPUTS_DIR, filename)
            with open(file_path, "rb") as f:
                data = f.read()

            storage_key, sha256_hash, file_size = await storage_manager.save_file(
                case_id=case.id,
                filename=filename,
                data=data
            )

            existing_ev = (await session.execute(
                select(Evidence).where(Evidence.case_id == case.id, Evidence.original_filename == filename)
            )).scalar_one_or_none()

            if not existing_ev:
                ev = Evidence(
                    id=str(uuid.uuid4()),
                    case_id=case.id,
                    evidence_type=ev_type,
                    original_filename=filename,
                    storage_key=storage_key,
                    file_size_bytes=file_size,
                    sha256_hash=sha256_hash,
                    mime_type=mime,
                    uploaded_by=lead_user.id,
                    is_classified=True,
                    authorized_departments=depts,
                    processing_status=ProcessingStatus.PENDING,
                    metadata_json=meta
                )
                session.add(ev)
                print(f"        [+] {filename:45s} | SHA-256: {sha256_hash[:16]}... | {ev_type.value}")
            else:
                print(f"        [i] {filename:45s} | (Already Registered in Vault)")

        await session.commit()

        # ====================================================================
        # 3. EXECUTE ENGINE ANALYSIS PIPELINE
        # ====================================================================
        print("\n[PHASE 4/4] Executing RRE 2.0 Departmental Reconstruction Pipeline ...")
        case_to_run = (await session.execute(select(Case).where(Case.id == case.id))).scalar_one()
        analysis_res = await run_case_analysis(
            db=session,
            case=case_to_run,
            user_id=lead_user.id,
            analysis_version=1
        )

        version = analysis_res.get("version", 1)
        matrix = analysis_res.get("execution_matrix", {})
        print(f"      --> Pipeline Execution Completed: Version {version} | Engines Executed: {len(matrix)}")

        # Pre-compile the Investigation Intelligence Dossier Report
        report_entity = await generate_case_report(
            db=session,
            case=case_to_run,
            user=lead_user,
            analysis_version=version
        )
        await session.commit()
        print(f"      --> Intelligence Dossier Compiled : Report ID {report_entity.id}")

        # Query summary figures
        candidate_entities = (await session.execute(
            select(CandidateEntity).where(CandidateEntity.case_id == case.id, CandidateEntity.analysis_version == version)
        )).scalars().all()

        source_timelines = (await session.execute(
            select(SourceTimeline).where(SourceTimeline.case_id == case.id, SourceTimeline.analysis_version == version)
        )).scalars().all()

        correlated_events = (await session.execute(
            select(CorrelatedTimelineEvent).where(CorrelatedTimelineEvent.case_id == case.id, CorrelatedTimelineEvent.analysis_version == version)
        )).scalars().all()

        hypotheses = (await session.execute(
            select(Hypothesis).where(Hypothesis.case_id == case.id, Hypothesis.analysis_version == version)
        )).scalars().all()

        gaps = (await session.execute(
            select(GapConflict).where(GapConflict.case_id == case.id, GapConflict.analysis_version == version)
        )).scalars().all()

        # Print Presentation Banner
        print("\n" + "=" * 84)
        print("   *** PRESENTATION CASE READY FOR SHOWCASE: SEC-2026-SHOWCASE ***")
        print("=" * 84)
        print(f"  Case Title            : {case.title}")
        print(f"  Case Number           : {case.case_number}")
        print(f"  Case UUID             : {case.id}")
        print(f"  Evidence Exhibits     : 9 Authentic Multimodal Items (CCTV, Macro, Print, Logs, Statements)")
        print(f"  Correlated Events     : {len(correlated_events)} Cross-Source Synchronized Timelines")
        print(f"  Candidate Entities    : {len(candidate_entities)} Linked Entities (Suspect, Guard, Vehicles)")
        print(f"  Synthesized Hypotheses: {len(hypotheses)} Multi-Scenario Reconstructions (L1 & L2 Audited)")
        print(f"  Gaps & Conflicts Radar: {len(gaps)} Coverage Blindspots & Discrepancies Monitored")
        print(f"  Dossier Report ID     : {report_entity.id} (Ready for 1-Click Judicial Export)")
        print("-" * 84)
        print("  KEY PRESENTATION DEMO USER CREDENTIALS:")
        print("     * Lead Investigator  : lead@police.gov      / leadpass123")
        print("     * Forensic Officer   : forensic@police.gov  / forensicpass123")
        print("     * Financial Analyst  : financial@police.gov / finpass123")
        print("     * Judicial / Legal   : legal@police.gov     / legalpass123")
        print("-" * 84)
        print("  HOW TO LAUNCH FOR YOUR PRESENTATION:")
        print("     1. Start Backend  : .venv\\Scripts\\python -m uvicorn app.main:app --reload --port 8000")
        print("     2. Start Frontend : cd frontend && npm run dev")
        print("     3. Open Browser   : http://localhost:5173")
        print("     4. Sign in with lead@police.gov / leadpass123 and select SEC-2026-SHOWCASE!")
        print("=" * 84 + "\n")


def main():
    generate_all_presentation_inputs()
    asyncio.run(setup_and_run_presentation_case())


if __name__ == "__main__":
    main()
