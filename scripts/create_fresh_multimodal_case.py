import os
import sys
import uuid
import hashlib
from datetime import datetime, timezone
import cv2
import numpy as np
from PIL import Image, ImageDraw

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

ASSETS_DIR = os.path.join(REPO_ROOT, "test_evidence_assets_multimodal_new")
os.makedirs(ASSETS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. GENERATE FRESH MULTIMODAL MEDIA ASSETS
# ---------------------------------------------------------------------------

def generate_cctv_video(filename: str, cam_name: str, base_time_str: str, motion_phase: str):
    filepath = os.path.join(ASSETS_DIR, filename)
    width, height = 640, 480
    fps = 15.0
    num_frames = 45  # 3.0 seconds

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

    for frame_idx in range(num_frames):
        frame = np.full((height, width, 3), 28, dtype=np.uint8)

        # Draw concrete floor perspective grid
        for y in range(220, height, 35):
            cv2.line(frame, (0, y), (width, y), (42, 42, 42), 1)
        for x in range(0, width, 50):
            cv2.line(frame, (x, 220), (int(x * 1.35 - 70), height), (42, 42, 42), 1)

        # Architectural features per camera angle
        if "BAY_04" in cam_name:
            # Loading dock roll-up shutter & exterior apron
            cv2.rectangle(frame, (140, 60), (500, 420), (65, 65, 65), 2)
            cv2.putText(frame, "LOADING BAY 04 - EXTERIOR APRON", (150, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)
            # Subject arriving with shoulder bag
            x_pos = int(180 + frame_idx * 3)
            cv2.rectangle(frame, (x_pos, 150), (x_pos + 85, 380), (0, 255, 0), 2)
            cv2.putText(frame, "DETECTION_01 [BAY_INBOUND]", (x_pos - 10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 0), 1)
        elif "VAULT_C" in cam_name:
            # Secure corridor & reinforced vault door
            cv2.rectangle(frame, (220, 100), (420, 430), (80, 80, 85), -1)
            cv2.rectangle(frame, (240, 120), (400, 430), (50, 50, 55), 2)
            cv2.putText(frame, "RESTRICTED VAULT C - SECURE ENCLOSURE", (130, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (140, 140, 160), 1)
            # Subject approaching vault hasp
            x_pos = int(160 + frame_idx * 2)
            cv2.rectangle(frame, (x_pos, 140), (x_pos + 80, 390), (0, 255, 0), 2)
            cv2.putText(frame, "DETECTION_01 [PROXIMITY_ALERT]", (x_pos - 15, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 165, 255), 1)
        else: # GATE_12
            # Perimeter fence & turnstile
            cv2.rectangle(frame, (100, 80), (540, 440), (60, 60, 60), 2)
            cv2.line(frame, (120, 370), (520, 370), (0, 0, 255), 2)
            cv2.putText(frame, "NORTH PERIMETER TURNSTILE - GATE 12", (140, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 220), 1)
            # Subject crossing outbound line
            x_pos = int(240 + frame_idx * 4)
            cv2.rectangle(frame, (x_pos, 130), (x_pos + 85, 370), (0, 255, 0), 2)
            cv2.putText(frame, "DETECTION_01 [OUTBOUND_EGRESS]", (x_pos - 10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 0), 1)

        # On-Screen Display (OSD) status bar
        cv2.rectangle(frame, (0, 0), (width, 32), (0, 0, 0), -1)
        sec = frame_idx // 15
        ms = (frame_idx % 15) * 66
        current_time_str = f"{base_time_str}:{sec:02d}.{ms:03d} UTC"
        cv2.putText(frame, f"REC [LIVE]  {cam_name}  {current_time_str}", (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 255, 255), 1)
        cv2.circle(frame, (615, 16), 5, (0, 0, 255), -1)

        out.write(frame)

    out.release()
    print(f"  [+] Generated video: {filename} ({os.path.getsize(filepath)} bytes)")

def generate_macro_scene_image(filename: str):
    filepath = os.path.join(ASSETS_DIR, filename)
    img = Image.new("RGB", (1200, 900), color=(40, 42, 46))
    draw = ImageDraw.Draw(img)

    # Steel door edge
    draw.rectangle([100, 150, 1100, 750], fill=(65, 68, 74), outline=(100, 105, 115), width=3)

    # Heavy industrial latch plate
    draw.rectangle([450, 300, 750, 600], fill=(30, 32, 36), outline=(160, 165, 175), width=4)
    draw.text((470, 320), "VAULT C AUXILIARY HASP", fill=(200, 200, 210))

    # Visible pry lever scratch mark
    draw.line([560, 420, 640, 480], fill=(220, 220, 230), width=6)
    draw.line([550, 430, 630, 490], fill=(180, 180, 190), width=4)
    # Paint flaking and metal deformation indicator
    draw.ellipse([540, 410, 660, 500], outline=(255, 60, 60), width=3)
    draw.text((480, 520), "MECHANICAL PRY STRIATION (17.5mm BEVEL)", fill=(255, 100, 100))

    # Forensic photomacrography metric scale
    draw.rectangle([800, 660, 1050, 710], fill=(255, 235, 60), outline=(0, 0, 0), width=2)
    draw.text((815, 675), "NIST CALIBRATED 10CM SCALE", fill=(0, 0, 0))
    for tick in range(800, 1050, 12):
        draw.line([tick, 695, tick, 710], fill=(0, 0, 0), width=1)

    # Forensic header banner
    draw.rectangle([0, 0, 1200, 50], fill=(18, 20, 24))
    draw.text((25, 15), "FORENSIC IDENTIFICATION SECTION - SCENE PHOTOMACROGRAPHY EXHIBIT", fill=(210, 225, 255))
    draw.text((950, 15), "2026-03-05 22:15:00 UTC", fill=(170, 175, 185))

    # Save with real EXIF tags
    exif = img.getexif()
    exif[0x010F] = "Nikon"               # Make
    exif[0x0110] = "D850 Forensic Macro" # Model
    exif[0x9003] = "2026:03:05 22:15:00" # DateTimeOriginal
    exif[0x9004] = "2026:03:05 22:15:00" # DateTimeDigitized

    img.save(filepath, "JPEG", quality=95, exif=exif)
    print(f"  [+] Generated forensic photo: {filename} ({os.path.getsize(filepath)} bytes)")

def generate_latent_fingerprint(filename: str):
    filepath = os.path.join(ASSETS_DIR, filename)
    img = Image.new("L", (700, 700), color=235)
    draw = ImageDraw.Draw(img)

    # Synthetic friction ridge patterns
    cx, cy = 350, 370
    for r in range(18, 220, 7):
        bbox = [cx - r, cy - r * 1.25, cx + r, cy + r * 1.25]
        draw.arc(bbox, start=25, end=155, fill=35, width=2)
        draw.arc(bbox, start=205, end=335, fill=45, width=2)

    # Smudge distortion from handle contact
    draw.rectangle([260, 320, 440, 390], fill=175)
    for i in range(25):
        draw.line([280 + i * 6, 320, 290 + i * 6, 390], fill=65, width=1)

    # Forensic card border & scale
    draw.rectangle([25, 25, 675, 675], outline=0, width=2)
    draw.text((45, 45), "LATENT FRICTION RIDGE CARD - LIFTED FROM VAULT C EXTERIOR HANDLE", fill=0)
    draw.text((45, 70), "CASE REF: SEC-2026-0842  |  EVIDENCE TECH: D. CHEN, CLPE", fill=50)
    draw.rectangle([45, 615, 345, 650], fill=255, outline=0, width=2)
    draw.text((60, 626), "CALIBRATED METRIC SCALE 1CM : 50PX", fill=0)

    img.save(filepath, "PNG")
    print(f"  [+] Generated latent print: {filename} ({os.path.getsize(filepath)} bytes)")

def generate_rfid_access_csv(filename: str):
    filepath = os.path.join(ASSETS_DIR, filename)
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
    print(f"  [+] Generated access log: {filename} ({os.path.getsize(filepath)} bytes)")

def generate_inventory_reconciliation_csv(filename: str):
    filepath = os.path.join(ASSETS_DIR, filename)
    csv_data = """sku,product_name,category,expected_stock_count,physical_count,unit_cost_usd,location_bin
SKU-OPT-100,100G Optical Transceiver Modules,TELECOM_HARDWARE,60,60,450.00,BIN-C-01
SKU-CAT-809,Industrial Platinum Catalyst Cylinders,PRECIOUS_MATERIALS,4,2,18500.00,BIN-C-VAULT-04
SKU-NVME-400,High-Density 32TB NVMe Server Drives,ENTERPRISE_STORAGE,24,24,890.00,BIN-C-02
SKU-SFP-28,25G SFP28 Direct Attach Copper Cable,CABLES_ACCESSORIES,150,150,35.00,BIN-C-03
SKU-PSU-1600,1600W Titanium Server Power Supply,POWER_INFRASTRUCTURE,18,18,320.00,BIN-C-05
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(csv_data)
    print(f"  [+] Generated inventory CSV: {filename} ({os.path.getsize(filepath)} bytes)")

def generate_witness_statement_text(filename: str):
    filepath = os.path.join(ASSETS_DIR, filename)
    statement = """SECURITY OFFICER FIRSTHAND OBSERVATION REPORT
INCIDENT ID: SEC-2026-0842
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
    print(f"  [+] Generated witness statement: {filename} ({os.path.getsize(filepath)} bytes)")

def generate_forensic_metallurgical_report(filename: str):
    filepath = os.path.join(ASSETS_DIR, filename)
    report = """FORENSIC PHYSICAL EVIDENCE & TOOLMARK EXAMINATION
LABORATORY REPORT #FLR-2026-03-902
EXAMINATION DATE: 2026-03-05 23:15 UTC
AGENCY CASE: SEC-2026-0842

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
    print(f"  [+] Generated metallurgical report: {filename} ({os.path.getsize(filepath)} bytes)")

# ---------------------------------------------------------------------------
# 2. INGEST CASE & EXHIBITS INTO DATABASE
# ---------------------------------------------------------------------------

async def setup_case_in_db():
    from app.database import AsyncSessionLocal
    from app.models.entities import Case, Evidence, User
    from app.models.enums import CaseType, CaseStatus, EvidenceType, ProcessingStatus
    from app.evidence.storage import storage_manager
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # Get lead investigator user
        user = (await session.execute(select(User).limit(1))).scalar_one_or_none()
        if not user:
            print("  [!] No user found in DB. Creating system investigator user...")
            user = User(
                id=str(uuid.uuid4()),
                email="lead.investigator@rre-depot.gov",
                full_name="Lead Investigator S. Chen",
                hashed_password="dummy",
                department="INVESTIGATION",
                role="LEAD_INVESTIGATOR"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # Check if case SEC-2026-0842 already exists
        existing_case = (await session.execute(
            select(Case).where(Case.case_number == "SEC-2026-0842")
        )).scalar_one_or_none()

        if existing_case:
            print(f"  [i] Case SEC-2026-0842 already exists (UUID: {existing_case.id}). Reusing.")
            case = existing_case
        else:
            case = Case(
                id=str(uuid.uuid4()),
                case_number="SEC-2026-0842",
                title="Security Incident Investigation: Apex Logistics Depot #7 - Vault C Perimeter & Stock Discrepancy",
                case_type=CaseType.THEFT,
                status=CaseStatus.CREATED,
                incident_location="Apex Logistics Depot #7, Sector B, Vault C",
                incident_time_observed=datetime(2026, 3, 5, 21, 18, 30, tzinfo=timezone.utc),
                incident_context={
                    "premises": "Apex Logistics Depot #7 - High-Value Secure Transit Hub",
                    "facility_sector": "Sector B, Corridor 3 & Vault C",
                    "alert_trigger": "Unscheduled door contact sensor trip & end-of-shift physical reconciliation variance",
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
            await session.commit()
            await session.refresh(case)
            print(f"  [+] Created fresh Case SEC-2026-0842 (UUID: {case.id})")

        # Manifest of exhibits to attach
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
            ("cctv_gate_perimeter_outbound.mp4", EvidenceType.CCTV, "video/mp4", ["INVESTIGATION"], {
                "camera_id": "CAM-12",
                "location": "North Perimeter Turnstile Gate 12",
                "start_time": "2026-03-05T21:26:15Z",
                "duration_seconds": 180.0,
                "fps": 15.0
            }),
            ("forensic_vault_hasp_macro.jpg", EvidenceType.IMAGE, "image/jpeg", ["FORENSIC"], {
                "capture_time": "2026-03-05T22:15:00Z",
                "camera_make": "Nikon",
                "camera_model": "D850 Forensic Macro",
                "has_damage": True,
                "forced_entry": True,
                "damage_target": "Vault C Auxiliary Hasp & Latch Plate",
                "sharpness": 142.5
            }),
            ("forensic_latent_impression_lift.png", EvidenceType.IMAGE, "image/png", ["FORENSIC"], {
                "capture_time": "2026-03-05T22:45:00Z",
                "impression_target": "Vault C Exterior Handle",
                "latent_method": "Black Magnetic Powder Lift",
                "sharpness": 88.0
            }),
            ("logistics_rfid_access_audit.csv", EvidenceType.TRANSACTION_RECORD, "text/csv", ["FINANCIAL", "INVESTIGATION"], {
                "sensor_type": "RFID_ACCESS_CONTROL",
                "period": "2026-03-05"
            }),
            ("depot_inventory_reconciliation.csv", EvidenceType.INVENTORY_RECORD, "text/csv", ["FINANCIAL"], {
                "ledger_type": "INVENTORY_RECONCILIATION",
                "period": "2026-03-05",
                "facility": "Apex Logistics Depot #7 - Vault C"
            }),
            ("security_officer_statement.txt", EvidenceType.WITNESS_STATEMENT, "text/plain", ["INVESTIGATION"], {
                "witness_name": "Officer David Kovacs",
                "role": "Shift Patrol Specialist",
                "interview_time": "2026-03-05T22:30:00Z"
            }),
            ("forensic_metallurgical_report.txt", EvidenceType.FORENSIC_REPORT, "text/plain", ["FORENSIC"], {
                "examiner": "Dr. Elena Rostova",
                "lab_reference": "FLR-2026-03-902",
                "date": "2026-03-05"
            })
        ]

        # Attach each exhibit
        for filename, ev_type, mime, depts, meta in exhibit_manifest:
            path = os.path.join(ASSETS_DIR, filename)
            with open(path, "rb") as f:
                data = f.read()

            storage_key, sha256_hash, file_size = await storage_manager.save_file(
                case_id=case.id,
                filename=filename,
                data=data
            )

            # Check if exhibit already exists
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
                    uploaded_by=user.id,
                    is_classified=True,
                    authorized_departments=depts,
                    processing_status=ProcessingStatus.PENDING,
                    metadata_json=meta
                )
                session.add(ev)
                print(f"  [+] Attached Exhibit: {filename} ({ev_type.value})")
            else:
                print(f"  [i] Exhibit already attached: {filename}")

        await session.commit()
        print(f"\n==========================================================================")
        print(f"  FRESH MULTIMODAL CASE CREATED & READY FOR EVALUATION")
        print(f"  Case Number : {case.case_number}")
        print(f"  Case UUID   : {case.id}")
        print(f"  Title       : {case.title}")
        print(f"  Exhibits    : 9 Genuine Multimodal Files Attached")
        print(f"  Status      : CREATED (Un-reconstructed; Waiting for user-driven run)")
        print(f"==========================================================================\n")

def generate_all_assets():
    generate_cctv_video("cctv_depot_bay4_exterior.mp4", "CAM-04 [BAY_04_EXTERIOR]", "2026-03-05 21:12", "INBOUND")
    generate_cctv_video("cctv_corridor_vault_interior.mp4", "CAM-09 [VAULT_C_CORRIDOR]", "2026-03-05 21:18", "PROXIMITY")
    generate_cctv_video("cctv_gate_perimeter_outbound.mp4", "CAM-12 [GATE_12_NORTH]", "2026-03-05 21:26", "OUTBOUND")
    generate_macro_scene_image("forensic_vault_hasp_macro.jpg")
    generate_latent_fingerprint("forensic_latent_impression_lift.png")
    generate_rfid_access_csv("logistics_rfid_access_audit.csv")
    generate_inventory_reconciliation_csv("depot_inventory_reconciliation.csv")
    generate_witness_statement_text("security_officer_statement.txt")
    generate_forensic_metallurgical_report("forensic_metallurgical_report.txt")

def main():
    print("\n--- Phase 1: Generating Fresh Media Assets ---")
    generate_all_assets()

    print("\n--- Phase 2: Ingesting into Database ---")
    import asyncio
    asyncio.run(setup_case_in_db())

if __name__ == "__main__":
    main()
