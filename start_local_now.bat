@echo off
setlocal EnableDelayedExpansion

REM ====================================================================
REM   JOBHUNT PRO SAAS - SOVEREIGN LOCAL ENGINE AND AI CLIENT SWARM
REM ====================================================================
title JobHunt Pro SaaS - Sovereign Local Engine
color 0B

REM 0. Force working directory to the batch script folder safely
cd /d "%~dp0"
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

REM 1. Initialize High-Performance Environment Variables and Directories
set "PYTHONPATH=%ROOT_DIR%"
set "FORCE_SQLITE=1"
set "PYTHONOPTIMIZE=1"
set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "SKIP_INSTALL=1"

if not exist "%ROOT_DIR%\data" mkdir "%ROOT_DIR%\data" >nul 2>nul
if not exist "%ROOT_DIR%\data\backups" mkdir "%ROOT_DIR%\data\backups" >nul 2>nul

REM Auto-provision .env if missing
if not exist "%ROOT_DIR%\.env" (
    if exist "%ROOT_DIR%\.env.example" (
        copy "%ROOT_DIR%\.env.example" "%ROOT_DIR%\.env" >nul 2>nul
        echo [*] Auto-created .env configuration from .env.example
    )
)

REM 2. Clean any stale processes holding port 8000 safely & purge old locks
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8000 .*LISTENING" 2^>nul') do (
    if "%%a" neq "0" taskkill /f /pid %%a >nul 2>nul
)
del /f /q "%TEMP%\jobhunt_*.lock" >nul 2>nul

REM 3. Detect Optimal Python interpreter (Priority: Local .venv -> Local .venv2 -> AppData Python312 -> Global PATH)
set "PY_EXE="

if exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    "%ROOT_DIR%\.venv\Scripts\python.exe" -c "import uvicorn, fastapi" >nul 2>nul
    if not errorlevel 1 (
        set "PY_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
        goto :START_ENGINE
    )
)

if exist "%ROOT_DIR%\.venv2\Scripts\python.exe" (
    "%ROOT_DIR%\.venv2\Scripts\python.exe" -c "import uvicorn, fastapi" >nul 2>nul
    if not errorlevel 1 (
        set "PY_EXE=%ROOT_DIR%\.venv2\Scripts\python.exe"
        goto :START_ENGINE
    )
)

if exist "C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe" -c "import uvicorn, fastapi" >nul 2>nul
    if not errorlevel 1 (
        set "PY_EXE=C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe"
        goto :START_ENGINE
    )
)

python -c "import uvicorn, fastapi" >nul 2>nul
if not errorlevel 1 (
    set "PY_EXE=python"
    goto :START_ENGINE
)

py -3.12 -c "import uvicorn, fastapi" >nul 2>nul
if not errorlevel 1 (
    set "PY_EXE=py -3.12"
    goto :START_ENGINE
)

py -3 -c "import uvicorn, fastapi" >nul 2>nul
if not errorlevel 1 (
    set "PY_EXE=py -3"
    goto :START_ENGINE
)

REM Fallback if not verified
if exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    set "PY_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

:START_ENGINE
cls
echo ================================================================================
echo   JOBHUNT PRO SAAS - 24/7 AUTONOMOUS SOVEREIGN ENGINE
echo ================================================================================
echo   [*] Root Workspace  : "%ROOT_DIR%"
echo   [*] Python Runtime  : "%PY_EXE%"
echo   [*] Local URL       : http://127.0.0.1:8000
echo   [*] Admin Authority : admin@jobhunt-pro.com
echo   [*] Deliverability  : 100%% Live MX and 365-Day Cooldown Guard (Active)
echo   [*] Auto-Browser    : Enabled (Auto-launches on ready)
echo ================================================================================
echo.
echo   Starting server and autonomous swarms...
echo.

REM Pre-clear port 8000 again to guarantee 100% clean bind
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8000 .*LISTENING" 2^>nul') do (
    if "%%a" neq "0" taskkill /f /pid %%a >nul 2>nul
)

"%PY_EXE%" "%ROOT_DIR%\run_local_server.py"

if errorlevel 1 (
    echo.
    echo ================================================================================
    echo   [!] Server stopped with exit code %ERRORLEVEL%.
    echo ================================================================================
    echo.
    echo Press any key to restart or close this window...
    pause >nul
)
exit /b 0
