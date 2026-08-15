@echo off
setlocal EnableDelayedExpansion

:: 0. Force working directory to the batch script's exact folder
cd /d "%~dp0"
set "ROOT_DIR=%~dp0"

:: 1. Clean any stale processes holding port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: 2. Set environment variables
set "PYTHONPATH=%~dp0"
set "FORCE_SQLITE=1"
set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "SKIP_INSTALL=1"

:: 3. Detect Python interpreter that has uvicorn
set "PY_EXE="

python -c "import uvicorn, fastapi" >nul 2>&1
if not errorlevel 1 (
    set "PY_EXE=python"
    goto :LAUNCH
)

if exist "C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe" -c "import uvicorn, fastapi" >nul 2>&1
    if not errorlevel 1 (
        set "PY_EXE=C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe"
        goto :LAUNCH
    )
)

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -c "import uvicorn, fastapi" >nul 2>&1
    if not errorlevel 1 (
        set "PY_EXE=%~dp0.venv\Scripts\python.exe"
        goto :LAUNCH
    )
)

set "PY_EXE=python"

:LAUNCH
echo ====================================================================
echo   STARTING JOBHUNT PRO LOCAL SOVEREIGN ENGINE (24/7 AI SWARM)
echo ====================================================================
echo [*] Working Folder  : %ROOT_DIR%
echo [*] Python Runtime  : !PY_EXE!
echo [*] Admin Privilege: samatou683@gmail.com
echo.

"!PY_EXE!" "%ROOT_DIR%run_local_server.py"

if errorlevel 1 (
    echo.
    echo ====================================================================
    echo [ERROR] Engine stopped. Press any key to exit...
    echo ====================================================================
)

pause
