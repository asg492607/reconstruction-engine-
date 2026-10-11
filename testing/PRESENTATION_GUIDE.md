# Reality Reconstruction Engine (RRE 2.0)

## Complete Presentation & Live Demonstration Guide

> **Case Showcase**: `SEC-2026-SHOWCASE`  
> **Title**: Apex Logistics Depot #7: Vault C Forced Entry & High-Value Inventory Discrepancy  
> **Location**: Apex Logistics Depot #7, Sector B, Restricted Vault Enclosure  
> **Incident Time**: March 5, 2026 @ 21:18:22 UTC  
> **Estimated Loss**: $37,000 USD (2x Industrial Platinum Catalyst Cylinders SKU-CAT-809)

---

## 🎯 Executive Pitch (30-Second Opening Hook)

> *"In modern criminal investigations, evidence is fragmented across disconnected silos: CCTV cameras, crime scene photos, RFID logs, inventory databases, and witness depositions. Traditional AI systems make wild guesses and hallucinate verdicts.
>
> **Reality Reconstruction Engine (RRE 2.0)** changes this: it enforces an **8-tier evidentiary separation**, preserves files with **SHA-256 cryptographic hashing**, correlates multimodal observations across independent departments, and subjects every reconstruction to **Two-Layer Validation**—deterministic physics checks and adversarial AI counter-challenge—while strictly upholding a **Non-Verdict principle**."*

---

## 🔑 Presentation Demo Logins

All users are pre-seeded in the database with their respective Department and Attribute-Based Access Control (ABAC) roles:

| Role / Badge | Login Email | Password | Department | What to Show in UI |
| :--- | :--- | :--- | :--- | :--- |
| **Lead Investigator** | `lead@police.gov` | `leadpass123` | `INVESTIGATION` | Full Command Center, Reconstruction Studio, DAG Planner, Gaps Radar, Report Export |
| **Forensic Specialist** | `forensic@police.gov` | `forensicpass123` | `FORENSIC` | Toolmark Macro Photo (17.5mm striation), Latent Fingerprint Card, NIST Metric Scales |
| **Financial Analyst** | `financial@police.gov` | `finpass123` | `FINANCIAL` | Inventory Stock Reconciliation Ledger, $37,000 Deficit Calculation, RFID Sensor Tripping |
| **Prosecutor / Judge** | `legal@police.gov` | `legalpass123` | `LEGAL` | Read-only Dossier, Evidence Hash Auditing, Courtroom Intelligence Report Export |

---

## 🎬 10-Minute Presentation Script & Live Walkthrough

### Act 1: Setting the Scene & The Problem (Minutes 0:00 – 2:00)

* **Say**:
  * *"Welcome everyone. Today we are demonstrating the Reality Reconstruction Engine on a real-world multi-sensor commercial theft: Case `SEC-2026-SHOWCASE`."*
  * *"At Apex Logistics Depot #7, an unscheduled sensor alarm sounded at Vault C. Two platinum catalyst cylinders worth $37,000 disappeared. We have 9 pieces of raw evidence across video, photography, biometric friction ridges, RFID telemetry, inventory ledgers, and witness testimony."*
* **Show**:
  * Open the Web UI at `http://localhost:5173`.
  * Log in with `lead@police.gov` / `leadpass123`.
  * Point out the active case card: **Apex Logistics Depot #7: Vault C Forced Entry & High-Value Inventory Discrepancy**.

---

### Act 2: Evidence Vault & Cryptographic Chain of Custody (Minutes 2:00 – 4:00)

* **Navigate to**: `Evidence Vault` module.
* **Point out**:
  * **SHA-256 Fingerprint**: Every exhibit has an immutable cryptographic hash computed on intake.
  * **Strict ABAC Routing**: Note how `forensic_vault_hasp_photomacrography.jpg` is automatically tagged for `FORENSIC`, while `depot_inventory_reconciliation.csv` is routed to `FINANCIAL`.
  * **Genuine Multimodal Exhibits**:
    * `1_cctv_bay04_inbound_arrival.mp4` (Surveillance footage with timestamp HUD)
    * `2_cctv_vault_c_approach_breach.mp4` (Restricted corridor proximity alert)
    * `3_cctv_gate12_north_outbound.mp4` (Turnstile egress)
    * `4_forensic_vault_hasp_photomacrography.jpg` (Macro photo showing pry marks + NIST 10cm ruler)
    * `5_forensic_latent_fingerprint_lift.png` (Latent friction ridge lift card)
    * `6_rfid_access_control_audit.csv` (Door contact trip & forced signal logs)
    * `7_depot_inventory_reconciliation.csv` ($37,000 stock variance)
    * `8_witness_officer_statement.txt` (Patrol officer deposition)
    * `9_metallurgical_laboratory_report.txt` (Laboratory toolmark report)
* **Key Talking Point**:
  * *"In RRE, evidence cannot be altered after upload. If even a single byte changes, the cryptographic hash fails validation, preventing evidence tampering."*

---

### Act 3: Departmental Workstations (Minutes 4:00 – 6:00)

* **Showcase Department Specialization**:
  * **Forensics Workstation**:
    * Highlight the toolmark macro photograph: mechanical pry striations measuring **17.5mm single-bevel implement** with calibrated NIST metric scale.
    * Mention the metallurgical report confirming trace copper-alloy transfer from the prying implement.
  * **Financial Analyst Ledger**:
    * Highlight SKU `SKU-CAT-809`: expected stock = 4, counted stock = 2, unit cost = $18,500. Total deficit: **$37,000 USD**.
    * Cross-reference with RFID logs: unscheduled contact trip at **21:18:22Z** and tamper alarm at **21:19:05Z**.
* **Key Talking Point**:
  * *"Specialists work independently in their domain-specific workstations. Forensic experts don't touch financial ledgers, and financial analysts don't interpret toolmarks. RRE respects domain boundaries."*

---

### Act 4: Correlated Timeline & Detective Board (Minutes 6:00 – 8:00)

* **Navigate to**: `Correlated Timeline` & `Detective Board`.
* **Demonstrate**:
  * **Synchronized Multimodal Timeline**:
    * `21:11:45 UTC`: Inbound vehicle hold at Bay 4 apron.
    * `21:12:00 – 21:15:00 UTC`: CCTV Bay 4 captures arrival of subject with shoulder sling bag.
    * `21:18:22 UTC`: Vault C corridor sensor tripped (UNSCHEDULED_ALARM).
    * `21:18:30 UTC`: CCTV Vault C corridor captures proximity breach at aux latch.
    * `21:19:05 UTC`: Door forced open tamper signal.
    * `21:22:00 UTC`: Officer David Kovacs encounters subject fleeing corridor.
    * `21:26:15 UTC`: CCTV Gate 12 captures outbound egress.
  * **Candidate Entity Resolution**:
    * Show how `CandidateEntity` links the individual observed in Bay 4 with the individual in Corridor 3 and the individual exiting Gate 12.
    * Link the latent fingerprint lifted from the handle to the physical entry act.

---

### Act 5: Reconstruction Studio & Two-Layer Validation (Minutes 8:00 – 10:00)

* **Navigate to**: `Reconstruction Studio`.
* **Demonstrate the Core Innovation**:
  * **Competing Hypotheses Matrix**:
    * **Scenario A (Direct Physical Removal)**: Forced mechanical entry via 17.5mm pry tool during patrol gap; high-value cylinders concealed in sling bag; outbound egress via Gate 12. Categorical Support Level: **`STRONG`**.
    * **Scenario B (Internal Collusion / Authorized Diversion)**: Insider staging using stolen badge credentials. Categorical Support Level: **`LIMITED`** (refuted by forced pry toolmarks and unscheduled alarm).
  * **Layer 1: Deterministic Physical Validation**:
    * Velocity limits: 2.1 m/s transit between Vault C and Gate 12 is physically feasible (within human walking/running bounds).
    * Temporal monotonicity: Events strictly follow an unbroken causal arrow of time.
  * **Layer 2: Adversarial AI Counter-Challenge (Defense Attorney Simulation)**:
    * The AI acts as an adversarial defense counsel, probing for gaps:
      * *"Notice the camera blind spot between Corridor 3 and Gate 12?"*
      * *"Can the system conclusively prove the contents of the sling bag without an x-ray scan?"*
    * RRE openly records these counter-arguments instead of sweeping them under the rug!
  * **Non-Verdict Safeguard**:
    * Point out the banner at the bottom: **"RRE does not render judicial verdicts or assign legal guilt. Determinations remain strictly human."**

---

### Act 6: Live Interactive Demonstration & Q&A (Minutes 10:00 – 12:00)

* **Demonstrate Copilot Chat (`CopilotChat.jsx`)**:
  * Test Prompt 1: *"Summarize the physical evidence linking the toolmark on Vault C to the entry implements."*
    * Watch Copilot cite Exhibit F-01 (17.5mm single-bevel bevel mark, copper-alloy trace) with exact source provenance citations!
  * Test Prompt 2 (Guardrail Test): *"Who is guilty of this crime?"*
    * **Watch the system enforce the Non-Verdict Guardrail live**: The Copilot politely declines to declare guilt, explaining that RRE assists evidentiary correlation while judicial determinations belong exclusively to human investigators and the courts!
* **Navigate to**: `Judicial Review / Export` (`DossierViewer.jsx`):
  * Show the pre-compiled, courtroom-ready **Investigation Intelligence Dossier Report** (`SEC-2026-SHOWCASE`).
  * Click **Print / Export PDF** to show the professional formatted dossier complete with investigator attestation signature block!

---

## 💡 Key Architectural Buzzwords & Strengths for Evaluation

| Concept | Why It Wows Evaluators / Judges |
| :--- | :--- |
| **8-Tier Evidentiary Separation** | Prevents confusing raw observations with legal conclusions (`Evidence → Observation → Finding → Claim → Correlated Event → Candidate Entity → Hypothesis → Verified Finding`). |
| **Two-Layer Validation** | Layer 1 enforces deterministic physical laws (speed, time monotonicity); Layer 2 simulates an adversarial defense counsel challenging the reconstruction. |
| **Categorical Support Levels** | Eliminates misleading fake percentages (e.g. "87.4% guilty") in favor of defendable legal categories: `STRONG`, `MODERATE`, `LIMITED`, `SPECULATIVE`. |
| **Cryptographic Immutability** | Every exhibit is fingerprinted with SHA-256 on intake; tamper-evident and chain-of-custody compliant. |
| **Strict Non-Verdict Design** | Protects the system against legal liability and ethical AI concerns by reserving judicial verdicts solely for humans. |

---

## ❓ Anticipated Questions & Winning Answers

### Q1: *"Why shouldn't the AI simply tell the investigator who is guilty?"*

> **Answer**: *"Under modern legal and constitutional frameworks (such as Daubert/Frye standards and the EU AI Act for high-risk systems), probabilistic machine verdicts are legally inadmissible and ethically hazardous. RRE's Non-Verdict design ensures every fact is traceable back to cryptographic source evidence, allowing human investigators and prosecutors to present a bulletproof, human-attested case in court."*

### Q2: *"How does the system ensure the AI didn't hallucinate a connection?"*

> **Answer**: *"RRE requires every Correlated Event and Candidate Entity link to possess explicit supporting evidence IDs. In addition, Layer 1 deterministic validation programmatically verifies physical velocity, temporal ordering, and spatial coexistence before any hypothesis is presented to the user."*

### Q3: *"Can this scale to hundreds of cameras and thousands of logs?"*

> **Answer**: *"Yes. RRE uses asynchronous FastAPI with SQLAlchemy 2.0 and supports PostgreSQL (`asyncpg`) and S3/MinIO storage. The 45-engine dispatcher evaluates a directed acyclic dependency graph (DAG), running independent departmental analysis in parallel."*
