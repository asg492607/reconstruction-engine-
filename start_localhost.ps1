# Reality Reconstruction Engine (RRE 2.0) - Localhost Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Reality Reconstruction Engine (RRE 2.0)" -ForegroundColor Cyan
Write-Host "  Starting Localhost Services (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# 1. Start FastAPI Backend
Write-Host "[1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 2

# 2. Start Vite Frontend
Write-Host "[2/2] Launching React Vite Frontend on http://127.0.0.1:5173 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev -- --host 127.0.0.1 --port 5173"

Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "  Localhost Environment Ready!" -ForegroundColor Green
Write-Host "  - Web App (Vite Dev Server): http://localhost:5173/" -ForegroundColor Green
Write-Host "  - Web App (FastAPI Direct):  http://localhost:8000/" -ForegroundColor Green
Write-Host "  - Interactive Swagger Docs:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
