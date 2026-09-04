# Reality Reconstruction Engine (RRE 2.0)
### Evidence Intelligence & Theft Reconstruction Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF.svg?style=flat&logo=vite)](https://vitejs.dev)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg?style=flat&logo=python)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.6%20Flash-4285F4.svg?style=flat&logo=google)](https://ai.google.dev/)
[![Firebase](https://img.shields.io/badge/Firebase-Auth-FFCA28.svg?style=flat&logo=firebase)](https://firebase.google.com/)
[![Tests](https://img.shields.io/badge/Tests-17%20Passing-brightgreen.svg?style=flat)]()

---

## 🔍 Overview

The **Reality Reconstruction Engine (RRE 2.0)** transforms scattered theft evidence into traceable observations, routes evidence to authorized specialist departments, correlates their independent findings across time and entities, and generates evidence-constrained hypotheses for investigator review.

Instead of treating AI output as factual conclusions, RRE enforces a rigorous, defendable architecture:
- **Evidence Vault & Integrity**: Every original file is preserved immutably with SHA-256 cryptographic hashing upon intake, informed by digital-evidence collection and preservation principles.
- **Strict Separation of Evidentiary Layers**: `Evidence → Observation → Finding → Claim → Correlated Event → Candidate Entity → Hypothesis → Verified Finding`.
- **Assisted Analysis & Human Verification**: Forensic and financial engines provide assisted measurement and feature extraction; human specialists review and record findings.
- **Two-Layer Validation & Self-Challenge**: Subjects hypotheses to deterministic evidence & consistency validation (Layer 1) and adversarial AI counter-evidence review (Layer 2).
- **Categorical Evidence Support Levels**: Replaces misleading percentage probability claims with transparent support levels (`STRONG`, `MODERATE`, `LIMITED`, `SPECULATIVE`) showing citations, contradictions, and coverage gaps.
- **Non-Verdict Design Principle**: RRE never determines individual guilt or renders judicial verdicts; admissibility and culpability remain strictly human and procedural determinations.

---

## 🏛️ System Flow & Architecture

```
                         RRE
                          │
                  CASE & POLICY
                          │
                          ▼
                  EVIDENCE VAULT
             hash + custody + metadata
                          │
                          ▼
              CLASSIFICATION ENGINE
                          │
                          ▼
                POLICY ROUTER
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   INVESTIGATION      FORENSICS         FINANCIAL
     ANALYSIS          ANALYSIS          ANALYSIS
        │                 │                 │
        ▼                 ▼                 ▼
   OBSERVATIONS      OBSERVATIONS      OBSERVATIONS
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                 PROVENANCE LAYER
                          │
                          ▼
                 ENTITY / EVENT
                    RESOLUTION
                          │
                          ▼
                 SOURCE TIMELINES
                          │
                          ▼
             CROSS-SOURCE CORRELATION
                          │
                          ▼
                  CLAIMS + EVENTS
                          │
                          ▼
              HYPOTHESIS GENERATION
                          │
                ┌─────────┼─────────┐
                ▼         ▼         ▼
             RULES       AI       GAPS &
           VALIDATION  CHALLENGE  CONFLICTS
                └─────────┼─────────┘
                          ▼
                   HUMAN REVIEW
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
          COPILOT      REPORT       ARCHIVE
```

---

## 🚀 Key Features

### 1. Modern React Light-Theme Frontend
- **Design Aesthetic**: Strict Blue & White light theme (`#2563eb` Royal Blue, `#ffffff` Crisp White, `#f8fafc` Ice Slate).
- **Responsive Navigation**: Mobile hamburger drawer, sticky glass header, adaptive grid cards.
- **Firebase Authentication**: Full email/password sign-in and registration with departmental role selection.

### 2. Specialized Department Dashboards
- **Lead Investigator Command**: Case metrics, leading hypotheses summary, high-severity coverage gaps, and 1-click reconstruction triggers.
- **Forensics Specialist Workstation**: Photographic toolmark inspection, assisted measurement, and evidence custody ledger.
- **Financial Analyst Ledger**: Inventory discrepancy calculations ($4,200 deficit for 3 iPhone 16 Pro Max units) and authorized registry matching.
- **External Legal Review & Export**: Controlled read-only access, evidence integrity ledger, and Evidence Reconstruction Report generation.

### 3. Investigation Modules
- **Evidence Vault**: Secure upload, policy routing, SHA-256 hash calculator, provenance inspector.
- **Correlated Timeline**: Synchronized chronological stream with department badges and source citations.
- **Reconstruction Studio**: Competing hypotheses evaluated across categorical Evidence Support Levels with Layer 1/Layer 2 consistency validation.
- **Gaps & Conflicts Radar**: Detects visual blind spots, unconfirmed intervals, and testimony discrepancies.
- **Candidate Entity Linkage Network**: Observation clusters and candidate entities with human-confirmed linkage workflows.
- **Investigation Copilot**: Dual-mode AI assistant (`EVIDENCE_ONLY` vs. `REASONING_MODE`) with Non-Verdict design guardrails.
- **Evidence Reconstruction Report**: Traceable investigative summary with print and JSON export.

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
LLM_MODEL="gemini-1.5-flash"
SECRET_KEY="your-jwt-secret-key"
```

### 3. Run the Application
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

All 17 automated integration and unit test suites pass, verifying end-to-end functionality across JWT & Firebase auth sync, ABAC policy enforcement, evidence routing, timeline correlation, multi-hypothesis reconstruction, and non-verdict safeguards.

---

## 📄 License
MIT License. Built for ethical, auditable, and transparent forensic intelligence.
