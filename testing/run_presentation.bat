@echo off
REM =========================================================================
REM Reality Reconstruction Engine (RRE 2.0) - Presentation Showcase Setup
REM =========================================================================
echo [RRE 2.0] Initializing Presentation Showcase Case (SEC-2026-SHOWCASE)...
cd /d "%~dp0\.."

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python testing\run_presentation_case.py
) else (
    python testing\run_presentation_case.py
)

echo.
echo [RRE 2.0] Setup completed!
pause
