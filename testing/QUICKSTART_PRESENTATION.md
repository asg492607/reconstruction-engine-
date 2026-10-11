# ⚡ 2-Minute Quick Start for Presentation Day

This quick start guide gets your presentation running in under 2 minutes.

---

## 🚀 Step 1: Initialize the Showcase Case (One Command)

In your terminal (from project root):

```powershell
.venv\Scripts\python testing\run_presentation_case.py
```

*What this does automatically:*
- Generates all 9 authentic multimodal inputs in `testing/inputs/`
- Seeds all presentation users into the database
- Preserves all exhibits with SHA-256 cryptographic digests in the Vault
- Runs the complete 45-engine analytical reconstruction pipeline
- Synthesizes competing hypotheses (L1 & L2 validated)
- Compiles the official Investigation Intelligence Dossier Report

---

## 🖥️ Step 2: Start the Servers

### Terminal 1: Backend API (Port 8000)
```powershell
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```
*Verify*: Open `http://localhost:8000/docs` in your browser.

### Terminal 2: Frontend Web App (Port 5173)
```powershell
cd frontend
npm run dev
```
*Verify*: Open `http://localhost:5173` in your browser.

---

## 🔑 Step 3: Log In to Present

Open your browser to: **`http://localhost:5173`**

Click **Sign In** and use any of these pre-seeded accounts:

| Role to Demonstrate | Email | Password |
| :--- | :--- | :--- |
| **Lead Investigator (Recommended)** | `lead@police.gov` | `leadpass123` |
| **Forensic Specialist** | `forensic@police.gov` | `forensicpass123` |
| **Financial Analyst** | `financial@police.gov` | `finpass123` |
| **Prosecutor / Judge** | `legal@police.gov` | `legalpass123` |

Select Case: **`SEC-2026-SHOWCASE`** (`Apex Logistics Depot #7: Vault C Forced Entry...`).

---

## 💡 Quick Presentation Flow (What to Click)

1. **Evidence Vault**: Show the 9 multimodal exhibits with SHA-256 hashes and department routing badges.
2. **Department Dashboards**: Show Forensics (17.5mm toolmark striation) and Financial ($37,000 deficit).
3. **Correlated Timeline**: Show multi-sensor chronological synchronization (RFID alarm -> CCTV breach -> Witness encounter).
4. **Reconstruction Studio**: Show competing hypotheses (Scenario A `STRONG` vs Scenario B `LIMITED`), Layer 1 physical velocity checks, and Layer 2 Adversarial AI challenge.
5. **Investigation Copilot**: Ask *"Summarize the physical evidence on Vault C"* and then ask *"Is the suspect guilty?"* to demonstrate the strict Non-Verdict legal guardrails!
6. **Judicial Dossier / Export**: Show the courtroom-ready printed report.

---

## 📁 Folder Structure Reference

```
testing/
├── inputs/                                     <-- All 9 genuine evidence files
│   ├── 1_cctv_bay04_inbound_arrival.mp4
│   ├── 2_cctv_vault_c_approach_breach.mp4
│   ├── 3_cctv_gate12_north_outbound.mp4
│   ├── 4_forensic_vault_hasp_photomacrography.jpg
│   ├── 5_forensic_latent_fingerprint_lift.png
│   ├── 6_rfid_access_control_audit.csv
│   ├── 7_depot_inventory_reconciliation.csv
│   ├── 8_witness_officer_statement.txt
│   └── 9_metallurgical_laboratory_report.txt
├── PRESENTATION_GUIDE.md                       <-- Full 10-minute presentation script & Q&A prep
├── CASE_DOSSIER.md                             <-- Official Law Enforcement intelligence brief
├── QUICKSTART_PRESENTATION.md                  <-- This 2-minute quick-start sheet
├── run_presentation_case.py                    <-- Turnkey Python script to run/re-seed
├── run_presentation.bat                        <-- 1-click Windows batch launcher
└── run_presentation.ps1                        <-- 1-click PowerShell launcher
```
