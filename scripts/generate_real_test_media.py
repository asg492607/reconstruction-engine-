import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_evidence_assets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_cctv_video(filename: str, cam_name: str, time_str: str, motion_type: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    width, height = 640, 480
    fps = 15.0
    num_frames = 45  # 3 seconds

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

    for frame_idx in range(num_frames):
        # Create security camera night-mode background
        frame = np.full((height, width, 3), 30, dtype=np.uint8)

        # Draw grid lines for floor/tiles
        for y in range(200, height, 40):
            cv2.line(frame, (0, y), (width, y), (45, 45, 45), 1)
        for x in range(0, width, 60):
            cv2.line(frame, (x, 200), (int(x * 1.3 - 50), height), (45, 45, 45), 1)

        # Draw architectural frame (doorway or shelf)
        if "ENTRANCE" in cam_name:
            cv2.rectangle(frame, (180, 80), (460, 440), (70, 70, 70), 2)
            cv2.putText(frame, "AUTOMATIC ENTRY 01", (190, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
            # Moving subject entering
            x_pos = int(220 + frame_idx * 3)
            cv2.rectangle(frame, (x_pos, 140), (x_pos + 90, 390), (0, 255, 0), 2)
            cv2.putText(frame, "TRACK_01 [CONF:0.94]", (x_pos, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        elif "AISLE" in cam_name or "DISPLAY" in cam_name:
            # Display pedestal
            cv2.rectangle(frame, (250, 220), (390, 420), (80, 80, 80), -1)
            cv2.rectangle(frame, (280, 170), (360, 220), (120, 120, 120), 2)
            cv2.putText(frame, "VALUABLE DISPLAY PEDESTAL", (210, 445), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (140, 140, 140), 1)
            # Subject reaching toward pedestal
            cv2.rectangle(frame, (170, 130), (270, 400), (0, 255, 0), 2)
            cv2.putText(frame, "TRACK_01 [PROXIMITY_ALERT]", (150, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)
        else: # EXIT
            cv2.rectangle(frame, (120, 100), (520, 450), (60, 60, 60), 2)
            cv2.line(frame, (150, 380), (490, 380), (0, 0, 255), 2)
            cv2.putText(frame, "EGRESS PERIMETER SENSOR", (160, 405), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 200), 1)
            # Subject crossing line
            x_pos = int(260 + frame_idx * 4)
            cv2.rectangle(frame, (x_pos, 120), (x_pos + 90, 380), (0, 255, 0), 2)
            cv2.putText(frame, "TRACK_01 [OUTBOUND]", (x_pos, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

        # CCTV OSD (On-Screen Display) header
        cv2.rectangle(frame, (0, 0), (width, 35), (0, 0, 0), -1)
        sec = frame_idx // 15
        ms = (frame_idx % 15) * 66
        current_time_str = f"{time_str}:{sec:02d}.{ms:03d} UTC"
        cv2.putText(frame, f"REC [LIVE]  {cam_name}  {current_time_str}", (15, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.circle(frame, (615, 18), 6, (0, 0, 255), -1)

        out.write(frame)

    out.release()
    print(f"Generated video: {filepath} ({os.path.getsize(filepath)} bytes)")

def generate_scene_image(filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    img = Image.new("RGB", (800, 600), color=(42, 44, 48))
    draw = ImageDraw.Draw(img)

    # Counter surface
    draw.rectangle([60, 320, 740, 560], fill=(70, 72, 78), outline=(120, 120, 130), width=2)
    # Empty display stand
    draw.rectangle([320, 220, 480, 320], fill=(30, 30, 35), outline=(160, 160, 180), width=3)
    draw.text((340, 260), "[EMPTY CRADLE]", fill=(220, 60, 60))

    # Cut tether wire
    draw.line([320, 290, 250, 340], fill=(180, 180, 190), width=4)
    draw.line([250, 340, 230, 350], fill=(240, 240, 250), width=3)
    # Tool cut mark indicator
    draw.ellipse([220, 340, 240, 360], outline=(255, 0, 0), width=2)
    draw.text((150, 365), "SEVERED TETHER END", fill=(255, 100, 100))

    # Evidence scale marker
    draw.rectangle([540, 420, 700, 460], fill=(255, 230, 50), outline=(0, 0, 0), width=2)
    draw.text((550, 430), "EVIDENCE MARKER #02", fill=(0, 0, 0))
    for tick in range(540, 700, 10):
        draw.line([tick, 450, tick, 460], fill=(0, 0, 0), width=1)

    # Forensic Watermark / Header
    draw.rectangle([0, 0, 800, 40], fill=(15, 15, 20))
    draw.text((20, 12), "FORENSIC IDENTIFICATION UNIT - CRIME SCENE PHOTOMACROGRAPHY", fill=(200, 220, 255))
    draw.text((640, 12), "2026-03-01 19:52 UTC", fill=(180, 180, 180))

    img.save(filepath, "JPEG", quality=95)
    print(f"Generated image: {filepath} ({os.path.getsize(filepath)} bytes)")

def generate_fingerprint_image(filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    img = Image.new("L", (600, 600), color=235)
    draw = ImageDraw.Draw(img)

    # Draw synthetic friction ridge arcs
    center_x, center_y = 300, 320
    for r in range(15, 180, 6):
        bbox = [center_x - r, center_y - r * 1.3, center_x + r, center_y + r * 1.3]
        draw.arc(bbox, start=30, end=150, fill=40, width=2)
        draw.arc(bbox, start=210, end=330, fill=50, width=2)

    # Smudge / distortion simulating latent recovery from glass
    draw.rectangle([220, 280, 380, 340], fill=180)
    for i in range(20):
        draw.line([240 + i * 6, 280, 250 + i * 6, 340], fill=70, width=1)

    # Forensic border and scale
    draw.rectangle([20, 20, 580, 580], outline=0, width=2)
    draw.text((40, 35), "LATENT PRINT CARD - RECOVERED FROM DISPLAY GLASS PERIMETER", fill=0)
    draw.text((40, 55), "CASE REF: CR-2026-0992  |  OPERATOR: FORENSIC INVESTIGATOR", fill=60)
    draw.rectangle([40, 530, 300, 560], fill=255, outline=0, width=2)
    draw.text((50, 538), "METRIC SCALE 1CM : 50PX", fill=0)

    img.save(filepath, "PNG")
    print(f"Generated fingerprint: {filepath} ({os.path.getsize(filepath)} bytes)")

def generate_pos_csv(filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    csv_data = """transaction_id,timestamp,register_id,cashier_id,sku,item_description,amount,payment_status
TX-20260301-101,2026-03-01T19:32:15Z,REG-01,EMP-882,SKU-4412,USB-C Braided Fast Cable 2M,24.99,SETTLED_APPROVED
TX-20260301-102,2026-03-01T19:35:40Z,REG-02,EMP-714,SKU-8821,Tempered Glass Screen Shield,19.50,SETTLED_APPROVED
TX-20260301-103,2026-03-01T19:39:10Z,REG-01,EMP-882,SKU-9011,Silicone MagSafe Phone Cover,45.00,SETTLED_APPROVED
TX-20260301-104,2026-03-01T19:46:22Z,REG-02,EMP-714,SKU-3120,Wireless Charging Pad 15W,39.99,SETTLED_APPROVED
TX-20260301-105,2026-03-01T19:53:05Z,REG-01,EMP-882,SKU-1044,Earbuds Silicone Replacement Tips,12.00,SETTLED_APPROVED
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(csv_data)
    print(f"Generated CSV: {filepath} ({os.path.getsize(filepath)} bytes)")

def generate_inventory_csv(filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    csv_data = """sku,item_name,category,expected_qty,counted_qty,delta,status,audit_notes
SKU-99214,Diamond Chronograph Luxury Watch,HIGH_VALUE_ELECTRONICS,1,0,-1,MISSING,Empty display mount located during 19:50 shelf check
SKU-4412,USB-C Braided Fast Cable 2M,ACCESSORIES,40,39,-1,NORMAL_SALE,Reconciled with TX-101
SKU-8821,Tempered Glass Screen Shield,ACCESSORIES,25,24,-1,NORMAL_SALE,Reconciled with TX-102
SKU-9011,Silicone MagSafe Phone Cover,ACCESSORIES,15,14,-1,NORMAL_SALE,Reconciled with TX-103
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(csv_data)
    print(f"Generated inventory: {filepath} ({os.path.getsize(filepath)} bytes)")

def generate_forensic_report(filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    report = """FORENSIC LABORATORY EXAMINATION REPORT
DIVISION: PHYSICAL EVIDENCE & TOOLMARK EXAMINATION SECTION
DATE OF INCIDENT: 2026-03-01
EXAMINATION DATE: 2026-03-01 20:30 UTC

EVIDENCE RECEIVED:
Item #01: One (1) severed braided stainless steel security cable, nominal diameter 2.0 mm, PVC outer jacket.
Recovered from: Display Counter Pedestal 03, Retail Floor.

MICROSCOPIC EXAMINATION:
Stereomicroscopic evaluation at 40x magnification reveals distinct shear and pinch tool marks across all steel filaments.
The cut edges exhibit asymmetric deformation characteristic of bypass-type diagonal cutting pliers.
Striation patterns show two opposing blade pinch marks with localized copper trace transfer on the terminal strand.

OPINION & FINDINGS:
1. The security cable did not fail from mechanical tension or fatigue.
2. The cable was mechanically severed using a hand-operated cutting tool (wire/diagonal cutters) with deliberate application of shear force.
3. The cutting event is estimated to have occurred immediately prior to property removal.

EXAMINER: Senior Forensic Specialist Dr. H. Lin, F-ABC
LABORATORY REPORT #FLR-2026-03-881A
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Generated forensic report: {filepath} ({os.path.getsize(filepath)} bytes)")

def generate_witness_statement(filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    statement = """WITNESS INTERVIEW STATEMENT
RECORDED BY: Detective R. Kelly, Investigation Division
DATE: 2026-03-01 20:10 UTC
WITNESS: Marcus Vance (Store Sales Floor Associate)

STATEMENT:
"I was working near the center electronics and luxury showcase area on the evening of March 1, 2026.
Around 7:42 PM, I noticed an individual in a dark jacket with a dark backpack lingering near the luxury watch pedestal.
The individual was looking around toward the ceiling corners as if checking camera coverage.
A customer approached me asking about phone cables, so I turned around toward Register 1 for approximately two minutes.
While assisting the customer, I heard a faint metallic snip sound from the direction of the display pedestal.
When I walked back over to Aisle 3 around 7:47 PM, the Diamond Chronograph Watch was gone, and the security tether was hanging loose.
I immediately alerted floor security and initiated an inventory discrepancy check."

I confirm this statement is true and accurate to the best of my recollection.
Signed: Marcus Vance
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(statement)
    print(f"Generated witness statement: {filepath} ({os.path.getsize(filepath)} bytes)")

if __name__ == "__main__":
    generate_cctv_video("cctv_entrance_real.mp4", "CAM-01 [ENTRANCE]", "2026-03-01 19:40", "ENTRY")
    generate_cctv_video("cctv_aisle_real.mp4", "CAM-03 [SHELF_AISLE]", "2026-03-01 19:44", "PROXIMITY")
    generate_cctv_video("cctv_exit_real.mp4", "CAM-05 [EXIT_TURNSTILE]", "2026-03-01 19:48", "EXIT")
    generate_scene_image("scene_shelf_severed_tether.jpg")
    generate_fingerprint_image("forensic_fingerprint_card.png")
    generate_pos_csv("pos_transactions_audit.csv")
    generate_inventory_csv("inventory_records.csv")
    generate_forensic_report("forensic_toolmark_report.txt")
    generate_witness_statement("witness_associate_statement.txt")
    print("All real evidence assets generated successfully!")
