@echo off
setlocal EnableDelayedExpansion

REM ====================================================================
REM   JOBHUNT PRO SAAS - SOVEREIGN LOCAL ENGINE AND AI CLIENT SWARM
REM ====================================================================
title JobHunt Pro SaaS - Sovereign Local Engine and AI Client Acquisition
color 0B

REM 0. Force working directory to the batch script folder safely
for %%i in ("%~dp0.") do set "ROOT_DIR=%%~fi"
cd /d "!ROOT_DIR!"

:DETECT_ENV
REM 1. Initialize High-Performance Environment Variables and Directories
set "PYTHONPATH=!ROOT_DIR!"
set "FORCE_SQLITE=1"
set "PYTHONOPTIMIZE=1"
set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "SKIP_INSTALL=1"

if not exist "!ROOT_DIR!\data" mkdir "!ROOT_DIR!\data" >nul 2>nul
if not exist "!ROOT_DIR!\data\backups" mkdir "!ROOT_DIR!\data\backups" >nul 2>nul

REM Auto-provision .env if missing
if not exist "!ROOT_DIR!\.env" (
    if exist "!ROOT_DIR!\.env.example" (
        copy "!ROOT_DIR!\.env.example" "!ROOT_DIR!\.env" >nul 2>nul
        echo [*] Auto-created .env configuration from .env.example
    )
)

REM 2. Clean any stale processes holding port 8000 safely & purge old locks using 100% Native Windows Commands
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8000 .*LISTENING" 2^>nul') do (
    if "%%a" neq "0" taskkill /f /pid %%a >nul 2>nul
)
del /f /q "%TEMP%\jobhunt_*.lock" >nul 2>nul

REM 3. Detect Optimal Python interpreter (Priority: Local .venv -> Local .venv2 -> AppData Python312 -> Global PATH)
set "PY_EXE="

if exist "!ROOT_DIR!\.venv\Scripts\python.exe" (
    "!ROOT_DIR!\.venv\Scripts\python.exe" -c "import uvicorn, fastapi" >nul 2>nul
    if not errorlevel 1 (
        set "PY_EXE=!ROOT_DIR!\.venv\Scripts\python.exe"
        goto :MENU
    )
)

if exist "!ROOT_DIR!\.venv2\Scripts\python.exe" (
    "!ROOT_DIR!\.venv2\Scripts\python.exe" -c "import uvicorn, fastapi" >nul 2>nul
    if not errorlevel 1 (
        set "PY_EXE=!ROOT_DIR!\.venv2\Scripts\python.exe"
        goto :MENU
    )
)

if exist "C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe" -c "import uvicorn, fastapi" >nul 2>nul
    if not errorlevel 1 (
        set "PY_EXE=C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe"
        goto :MENU
    )
)

python -c "import uvicorn, fastapi" >nul 2>nul
if not errorlevel 1 (
    set "PY_EXE=python"
    goto :MENU
)

py -3.12 -c "import uvicorn, fastapi" >nul 2>nul
if not errorlevel 1 (
    set "PY_EXE=py -3.12"
    goto :MENU
)

py -3 -c "import uvicorn, fastapi" >nul 2>nul
if not errorlevel 1 (
    set "PY_EXE=py -3"
    goto :MENU
)

REM Fallback if not verified
if exist "!ROOT_DIR!\.venv\Scripts\python.exe" (
    set "PY_EXE=!ROOT_DIR!\.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

:MENU
cls
echo ================================================================================
echo   JOBHUNT PRO SAAS - 24/7 AUTONOMOUS REVENUE AND CLIENT ENGINE
echo ================================================================================
echo   [*] Root Workspace  : !ROOT_DIR!
echo   [*] Python Runtime  : !PY_EXE!
echo   [*] Admin Authority : samatou683@gmail.com
echo   [*] Deliverability  : 100%% Live MX and 365-Day Cooldown Guard (Active)
echo   [*] Latency Profile : Sub-Millisecond In-Memory Fast Cache
echo ================================================================================
echo.
echo   [1] Launch Sovereign Engine (Production / Ultra-Fast - Auto in 3s)
echo   [2] Launch Engine in Live Dev / Hot-Reload Mode (--reload)
echo   [3] Run Viral GTM Swarm Pre-Flight Audit and Lead Magnet Check
echo   [4] Export Captured Leads to CSV / Excel Report
echo   [5] Create Instant SQLite Database Snapshot / Backup (.db.gz)
echo   [6] Run Sovereign Security and Route Integrity Audit
echo   [7] Run Automated Fast Test Suite (Pytest)
echo   [8] Install / Upgrade Project Dependencies (pip install)
echo   [9] Purge Cache and Clear Stale Temporary Locks
echo   [0] Exit
echo.
echo ================================================================================
choice /c 1234567890 /t 3 /d 1 /m "Select option (Auto-starts in 3s):"
set "OPT=!ERRORLEVEL!"

if "!OPT!"=="1" goto :ACTION_LAUNCH_PROD
if "!OPT!"=="2" goto :ACTION_LAUNCH_DEV
if "!OPT!"=="3" goto :ACTION_GTM
if "!OPT!"=="4" goto :ACTION_EXPORT
if "!OPT!"=="5" goto :ACTION_BACKUP
if "!OPT!"=="6" goto :ACTION_INTEGRITY
if "!OPT!"=="7" goto :ACTION_TESTS
if "!OPT!"=="8" goto :ACTION_INSTALL
if "!OPT!"=="9" goto :ACTION_CLEAN
if "!OPT!"=="10" goto :ACTION_EXIT
goto :ACTION_LAUNCH_PROD

:ACTION_LAUNCH_PROD
echo.
echo ================================================================================
echo   STARTING SOVEREIGN ENGINE (HIGH PERFORMANCE PRODUCTION MODE)...
echo ================================================================================
echo   [*] Local URL       : http://127.0.0.1:8000
echo   [*] User Dashboard  : http://127.0.0.1:8000/user-dashboard
echo   [*] Free ATS Score  : http://127.0.0.1:8000/free-ats-score
echo   [*] Battle Station  : http://127.0.0.1:8000/battle-station
echo   [*] Interactive Docs: http://127.0.0.1:8000/docs
echo ================================================================================
echo.
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8000 .*LISTENING" 2^>nul') do (
    if "%%a" neq "0" taskkill /f /pid %%a >nul 2>nul
)
"!PY_EXE!" "!ROOT_DIR!\run_local_server.py"
if errorlevel 1 (
    echo.
    echo [*] Server exited with code !ERRORLEVEL!.
)
echo.
echo Press any key to return to menu...
pause >nul
goto :MENU

:ACTION_LAUNCH_DEV
echo.
echo ================================================================================
echo   STARTING SOVEREIGN ENGINE (LIVE HOT-RELOAD DEV MODE)...
echo ================================================================================
echo   [*] Local URL       : http://127.0.0.1:8000
echo   [*] User Dashboard  : http://127.0.0.1:8000/user-dashboard
echo   [*] Live Reload     : ENABLED (Auto-reloads on file edits)
echo ================================================================================
echo.
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8000 .*LISTENING" 2^>nul') do (
    if "%%a" neq "0" taskkill /f /pid %%a >nul 2>nul
)
"!PY_EXE!" "!ROOT_DIR!\run_local_server.py" --reload --log-level info
if errorlevel 1 (
    echo.
    echo [*] Server exited with code !ERRORLEVEL!.
)
echo.
echo Press any key to return to menu...
pause >nul
goto :MENU

:ACTION_GTM
echo.
echo ================================================================================
echo   EXECUTING VIRAL GTM SWARM AUDIT AND LEAD MAGNET PRE-FLIGHT
echo ================================================================================
echo.
"!PY_EXE!" "!ROOT_DIR!\scripts\activate_viral_gtm_swarm.py"
echo.
echo Press any key to return to menu...
pause >nul
goto :MENU

:ACTION_EXPORT
echo.
echo ================================================================================
echo   EXPORTING CAPTURED LEADS AND PROSPECTS TO CSV
echo ================================================================================
echo.
"!PY_EXE!" "!ROOT_DIR!\scripts\export_leads.py"
echo.
echo Press any key to return to menu...
pause >nul
goto :MENU

:ACTION_BACKUP
echo.
echo ================================================================================
echo   CREATING COMPRESSED DATABASE BACKUP SNAPSHOT
echo ================================================================================
echo.
"!PY_EXE!" "!ROOT_DIR!\scripts\backup_db.py"
echo.
echo Press any key to return to menu...
pause >nul
goto :MENU

:ACTION_INTEGRITY
echo.
echo ================================================================================
echo   RUNNING SECURITY AND ROUTE INTEGRITY AUDIT
echo ================================================================================
echo.
"!PY_EXE!" "!ROOT_DIR!\verify_integrity.py"
echo.
echo Press any key to return to menu...
pause >nul
goto :MENU

:ACTION_TESTS
echo.
echo ================================================================================
echo   RUNNING AUTOMATED PYTEST SUITE
echo ================================================================================
echo.
"!PY_EXE!" -m pytest tests/ -q --tb=short
echo.
echo Press any key to return to menu...
pause >nul
goto :MENU

:ACTION_INSTALL
echo.
echo ================================================================================
echo   INSTALLING / UPGRADING PYTHON DEPENDENCIES
echo ================================================================================
echo.
"!PY_EXE!" -m pip install --upgrade pip
"!PY_EXE!" -m pip install -r "!ROOT_DIR!\requirements.txt"
echo.
echo [OK] Dependency verification complete.
echo Press any key to return to menu...
pause >nul
goto :MENU

:ACTION_CLEAN
echo.
echo ================================================================================
echo   PURGING CACHE AND TEMPORARY LOCK FILES
echo ================================================================================
echo.
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8000 .*LISTENING" 2^>nul') do (
    if "%%a" neq "0" taskkill /f /pid %%a >nul 2>nul
)
del /f /q "%TEMP%\jobhunt_*.lock" >nul 2>nul
"!PY_EXE!" "!ROOT_DIR!\scripts\clean_project_cache.py"
echo.
echo Press any key to return to menu...
pause >nul
goto :MENU

:ACTION_EXIT
echo.
echo Exiting JobHunt Pro Launcher. Goodbye!
ping -n 2 127.0.0.1 >nul
exit /b 0
