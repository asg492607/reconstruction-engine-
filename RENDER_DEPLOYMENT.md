# Reality Reconstruction Engine (RRE 2.0)

## Render Free Tier Backend Deployment Guide

This guide walks you through deploying the **Reality Reconstruction Engine (RRE 2.0) Backend API** on **Render's Free Tier** in under 5 minutes.

---

### Architectural Overview on Render Free Tier

Render's Free Tier grants **1 Free Web Service** with:

- **512 MB RAM**
- **0.1 vCPU**
- Automatic spin-down after 15 minutes of inactivity (spins back up in ~30 seconds on the next request).

The RRE 2.0 Backend is built with **FastAPI**, **SQLAlchemy (Async)**, and **Pydantic**:

- Full REST API with automated Swagger OpenAPI documentation at `/docs`.
- Built-in CORS support allowing frontend connections from localhost or any hosted UI.
- Automated database creation and default law enforcement account seeding upon service startup.

---

## Method 1: 1-Click Blueprint Deploy (Recommended)

Render provides native **Infrastructure as Code** support via the included [`render.yaml`](./render.yaml).

### Steps

1. Push this repository to your **GitHub** or **GitLab** account on branch `V1`.
2. Log in to [dashboard.render.com](https://dashboard.render.com/).
3. Click the **"New +"** button at the top right and select **"Blueprint"**.
4. Connect your repository.
5. Render will automatically detect [`render.yaml`](./render.yaml).
6. Set the optional environment variable `GEMINI_API_KEY` (enter your Google AI Studio API key).
7. Click **"Apply"**.
8. Render will run `build.sh`, install all backend dependencies, initialize the database schema, and launch the service!

---

## Method 2: Manual Web Service Setup

If you prefer configuring the Web Service manually via Render's dashboard:

1. Click **"New +"** $\rightarrow$ **"Web Service"**.
2. Connect your Git repository.
3. Configure the following fields:
   - **Name**: `reality-reconstruction-engine-api`
   - **Region**: `Oregon (US West)` or `Frankfurt (EU)`
   - **Branch**: `V1`
   - **Language / Runtime**: `Python 3`
   - **Build Command**: `bash ./build.sh`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free` ($0/mo)

4. Click **"Advanced"** and add these **Environment Variables**:

| Variable Key | Value | Purpose |
| --- | --- | --- |
| `PYTHON_VERSION` | `3.11.9` | Sets standard Python runtime |
| `ENVIRONMENT` | `production` | Production environment mode |
| `DEBUG` | `false` | Disables debug query printing |
| `STORAGE_BACKEND` | `LOCAL` | Uses local disk for evidence vault |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/rre.db` | Free embedded database |
| `SECRET_KEY` | *(Click "Generate" or enter random string)* | JWT auth secret |
| `GEMINI_API_KEY` | *(Your Gemini API Key)* | Multimodal OCR & Copilot |
| `LLM_MODEL` | `gemini-2.5-flash` | Fast low-latency model |
| `LLM_PROVIDER` | `AUTO` | Auto-routes between Gemini & local engines |

5. Under **Health Check Path**, enter: `/health`
6. Click **"Create Web Service"**.

---

## Pre-Seeded Law Enforcement Accounts

The build and startup script automatically initializes default department accounts into the database:

| Role | Email | Password |
| --- | --- | --- |
| **Lead Investigator** | `lead@police.gov` | `leadpass123` |
| **Forensic Examiner** | `forensic@police.gov` | `forensicpass123` |
| **Financial Analyst** | `financial@police.gov` | `finpass123` |
| **Investigative Detective** | `investigator@police.gov` | `invpass123` |
| **Legal / Judicial Magistrate** | `legal@police.gov` | `legalpass123` |
| **System Administrator** | `admin@police.gov` | `adminpass123` |

---

## Verifying Your Backend Deployment

Once Render displays **"Live"**:

1. Open your assigned URL (e.g. `https://reality-reconstruction-engine-api.onrender.com/`).
2. You will receive an immediate JSON status indicating the backend is online:
   - Root URL `/`: JSON service directory and available routes.
   - Interactive Swagger API Documentation: `/docs`.
   - ReDoc Documentation: `/redoc`.
   - Service Health Check: `/health`.
3. In your React frontend (`frontend/.env` or deployment), set:
   `VITE_API_BASE_URL=https://reality-reconstruction-engine-api.onrender.com`

---

## Free Tier Tips & Gotchas

- **Inactivity Spin-down**: On Render's free tier, services spin down after 15 minutes of inactivity. When you send a request after dormancy, the first request may take ~30-40 seconds to spin up.
- **Persistent vs Ephemeral Data**: Local SQLite files (`data/rre.db`) and uploaded files in `storage/` persist during normal operation. If you restart or redeploy the service, Render resets the free ephemeral container; the startup script automatically re-seeds the default accounts and cases. If you want permanent persistence, you can connect a Render PostgreSQL instance (`DATABASE_URL`), which is automatically converted to `postgresql+asyncpg://` without any code changes.
