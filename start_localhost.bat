@echo off
echo ===================================================
echo   Reality Reconstruction Engine (RRE 2.0)
echo   Starting Localhost Services (Backend + Frontend)
echo ===================================================

echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "RRE-Backend" cmd /k ".venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload"

ping -n 3 127.0.0.1 >nul

echo [2/2] Launching Vite Frontend on http://127.0.0.1:5173 ...
start "RRE-Frontend" cmd /k "cd frontend && npm run dev -- --host 127.0.0.1 --port 5173"

echo.
echo ===================================================
echo   Localhost Environment Ready!
echo   - Web Application: http://localhost:5173/ (or http://localhost:8000/)
echo   - Interactive API Docs: http://localhost:8000/docs
echo ===================================================
