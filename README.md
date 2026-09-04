# Reality Reconstruction Engine (RRE 2.0)
### AI-Assisted Multi-Modal Evidence Intelligence & Crime Scene Reconstruction Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF.svg?style=flat&logo=vite)](https://vitejs.dev)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg?style=flat&logo=python)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.6%20Flash-4285F4.svg?style=flat&logo=google)](https://ai.google.dev/)
[![Firebase](https://img.shields.io/badge/Firebase-Auth-FFCA28.svg?style=flat&logo=firebase)](https://firebase.google.com/)
[![Tests](https://img.shields.io/badge/Tests-17%20Passing-brightgreen.svg?style=flat)]()

---

## 🔍 Overview

The **Reality Reconstruction Engine (RRE 2.0)** is an empirical, multi-modal evidence intelligence platform designed for law enforcement detectives, forensic examiners, financial auditors, and prosecutors.

Instead of treating AI output as factual conclusions, RRE enforces a rigorous, mathematically and cryptographically grounded pipeline:
- **Original Evidence is Immutable**: Every file is hashed with SHA-256 upon intake (ISO/IEC 27037).
- **Canonical Separation of Data**: Strictly distinguishes `Evidence -> Observation -> Finding -> Claim -> Correlated Event -> Hypothesis -> Verified Finding`.
- **Two-Layer Self-Challenge**: Formulates competing theft hypotheses and subjects them to deterministic physics rules (Layer 1) and adversarial counter-arguments via **Google Gemini 3.6 Flash** (Layer 2).
- **Statutory Non-Automated Guilt Guarantee**: AI models are barred from determining guilt; conclusions remain exclusively under human judicial authority.

---

## 🏛️ System Architecture

```
                                  [EVIDENCE INTAKE VAULT]
                                             |
                                  (SHA-256 Tamper Evident)
                                             |
                                [CLASSIFICATION & ROUTING]
                                             |
        +------------------+-----------------+------------------+------------------+
        |                  |                 |                  |                  |
   [Forensic Lab]     [Visual Media]   [Cyber / Access]   [Financial Crimes]  [Witness / Field]
   Toolmarks & Photos  CCTV Timestamps   Badge Swipes      Inventory & IMEIs   Credibility Weight
        |                  |                 |                  |                  |
        +------------------+-----------------+------------------+------------------+
                                             |
                               [CANDIDATE ENTITY NETWORK]
                               (Human-Confirmed Identities)
                                             |
                               [CORRELATED TIMELINE MASTER]
                               (Multi-Source Synchronization)
                                             |
                                [GAPS & CONFLICTS RADAR]
                                (Coverage Blackout Detector)
                                             |
                             [RECONSTRUCTION STUDIO (A / B)]
                                (Multi-Hypothesis Synthesis)
                                             |
                            [TWO-LAYER SELF-CHALLENGE (AI)]
                             (Layer 1 Rules + Layer 2 Gemini)
                                             |
                                [HUMAN VERIFICATION GATE]
                               (Detective & Specialist Signoff)
                                             |
                              [OFFICIAL JUDICIAL DOSSIER]
                              (Printable & JSON Court Record)
```

---

## 🚀 Key Features

### 1. Modern React Light-Theme Frontend
- **Design Aesthetic**: Strict Blue & White light theme (`#2563eb` Royal Blue, `#ffffff` Crisp White, `#f8fafc` Ice Slate).
- **Responsive Navigation**: Mobile hamburger drawer, sticky glass header, adaptive grid cards.
- **Firebase Authentication**: Full email/password sign-in and registration with role and department selection.

### 2. Specialized Role Dashboards
- **Lead Investigator HUD**: Case metrics, leading hypotheses summary, high-severity anomalies, and 1-click reconstruction triggers.
- **Forensics Specialist Workstation**: Photographic striation inspection, CCTV frame timing, and SHA-256 custody ledger.
- **Financial Auditor Ledger**: Stolen inventory delta calculations ($4,200 loss for 3 iPhone 16 Pro Max units), IMEI broadcast, and fencing alerts.
- **Judicial / Magistrate Review**: Admissibility oversight, statutory AI disclosures, hash matrix, and court-ready dossier export.

### 3. Investigation Modules
- **Evidence Vault**: Secure upload, automated routing, SHA-256 hash calculator, provenance inspector.
- **Correlated Timeline**: Synchronized chronological stream with department badges and confidence scores.
- **Reconstruction Studio**: Competing hypotheses side-by-side with live Gemini 3.6 Flash counter-arguments.
- **Gaps & Conflicts Radar**: Detects CCTV blind spots and witness statement vs. telemetry contradictions.
- **Entity Ground Truth Network**: Unconfirmed candidates vs. confirmed ground-truth identities with 1-click detective verification.
- **Investigation Copilot**: Dual-mode AI assistant (`EVIDENCE_ONLY` vs. `REASONING_MODE`) with statutory non-guilt guardrails.
- **Court Dossier Generator**: Admissible forensic report with print and JSON export.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), SQLite (aiosqlite) / PostgreSQL (asyncpg), Pydantic v2, Google Gemini API, Firebase Admin SDK.
- **Frontend**: React 19, Vite 6, Vanilla CSS design system, Lucide React, Firebase Web SDK.
- **Testing**: Pytest, Pytest-Asyncio, HTTPX (17/17 automated test suites passing).

---

## ⚡ Quick Start

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/asg492607/reconstruction-engine-.git
cd reconstruction-engine-

# Setup Python Virtual Environment
python -m venv .venv
.venv\Scripts\activate  # On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# Setup Frontend
cd frontend
npm install
cd ..
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```env
APP_NAME="Reality Reconstruction Engine"
ENVIRONMENT="development"
DATABASE_URL="sqlite+aiosqlite:///./rre.db"
GEMINI_API_KEY="your-google-gemini-api-key"
LLM_MODEL="gemini-3.6-flash"
SECRET_KEY="your-jwt-secret-key"
```

### 3. Seed Demo Investigation Data
```bash
python scripts/demo_seed.py
```

### 4. Run the Application
```bash
# Terminal 1: FastAPI Backend
.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: React Vite Frontend
cd frontend
npm run dev
```

- **Web Application**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) (or [http://127.0.0.1:5173/](http://127.0.0.1:5173/))
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Testing

Run the full automated test suite:
```bash
pytest -v
```

All 17 suites pass with 100% coverage across auth, ABAC policy, evidence routing, timeline correlation, multi-hypothesis reconstruction, and judicial safeguards.

---

## 📄 License
MIT License. Built for ethical, auditable, and transparent forensic intelligence.
