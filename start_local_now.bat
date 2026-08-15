@echo off
chcp 65001 >nul
title JobHunt Pro Local Sovereign Engine v1 — 24/7 Autonomous AI Outreach
color 0B
cls

cd /d "%~dp0"

echo ====================================================================
echo    ⚡ STARTING JOBHUNT PRO LOCAL SOVEREIGN ENGINE (24/7 AI SWARM)
echo ====================================================================
echo.

:: 1. Clean any stale processes holding port 8000 gracefully
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: 2. Set environment variables for local high-velocity execution
set "PYTHONPATH=%~dp0"
set "FORCE_SQLITE=1"
set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "SKIP_INSTALL=1"

:: 3. Detect Python interpreter
set "PY_EXE="
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0.venv\Scripts\python.exe"
) else if exist "%~dp0.venv2\Scripts\python.exe" (
    set "PY_EXE=%~dp0.venv2\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if not errorlevel 1 (
        set "PY_EXE=python"
    ) else (
        set "PY_EXE=py"
    )
)

echo [*] Python Runtime  : %PY_EXE%
echo [*] Admin Privilege: samatou683@gmail.com
echo [*] Cloud Engine    : Permanent 24/7 $0 AI Swarm + Sub-ms Cache Active
echo.

:: 4. Launch engine directly
"%PY_EXE%" "%~dp0run_local_server.py"

if errorlevel 1 (
    echo.
    echo ====================================================================
    echo [ERROR] Engine exited with error code. Checking PowerShell fallback...
    echo ====================================================================
    if exist "%~dp0start_engine.ps1" (
        powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_engine.ps1"
    )
)

echo.
echo ====================================================================
echo [Engine Monitor Stopped] Press any key to exit window...
echo ====================================================================
pause
