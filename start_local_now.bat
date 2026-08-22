@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ==============================================================================
REM   JOBHUNT PRO SAAS - TITANIUM AUTONOMOUS SOVEREIGN LAUNCHER (v2026.1)
REM ==============================================================================
title JobHunt Pro SaaS - Sovereign Autonomous Engine
color 0B

cd /d "%~dp0"
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

set "PYTHONPATH=%ROOT_DIR%"
set "FORCE_SQLITE=1"
set "PYTHONOPTIMIZE=1"
set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "SKIP_INSTALL=1"
set "PORT=8000"
set "SITE_URL=http://127.0.0.1:8000"
set "APP_BASE_URL=http://127.0.0.1:8000"

if not exist "%ROOT_DIR%\data" mkdir "%ROOT_DIR%\data" >nul 2>nul
if not exist "%ROOT_DIR%\data\backups" mkdir "%ROOT_DIR%\data\backups" >nul 2>nul
if not exist "%ROOT_DIR%\data\blog" mkdir "%ROOT_DIR%\data\blog" >nul 2>nul
if not exist "%ROOT_DIR%\logs" mkdir "%ROOT_DIR%\logs" >nul 2>nul

if not exist "%ROOT_DIR%\.env" (
    if exist "%ROOT_DIR%\.env.example" (
        copy "%ROOT_DIR%\.env.example" "%ROOT_DIR%\.env" >nul 2>nul
        echo [*] Auto-created sovereign .env configuration from .env.example
    )
)

REM Free lingering port 8000 and 8001 processes
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8000 .*LISTENING" 2^>nul') do (
    if "%%a" neq "0" taskkill /f /pid %%a >nul 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8001 .*LISTENING" 2^>nul') do (
    if "%%a" neq "0" taskkill /f /pid %%a >nul 2>nul
)
del /f /q "%TEMP%\jobhunt_*.lock" >nul 2>nul

set "PY_EXE="
if exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    set "PY_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
    goto :FOUND_PYTHON
)
if exist "%ROOT_DIR%\.venv2\Scripts\python.exe" (
    set "PY_EXE=%ROOT_DIR%\.venv2\Scripts\python.exe"
    goto :FOUND_PYTHON
)
if exist "C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe" (
    set "PY_EXE=C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe"
    goto :FOUND_PYTHON
)
if exist "C:\Users\samde\AppData\Local\Programs\Python\Python311\python.exe" (
    set "PY_EXE=C:\Users\samde\AppData\Local\Programs\Python\Python311\python.exe"
    goto :FOUND_PYTHON
)
where python >nul 2>nul
if not errorlevel 1 (
    for /f "delims=" %%i in ('where python') do (
        if not defined PY_EXE set "PY_EXE=%%i"
    )
    goto :FOUND_PYTHON
)
where py >nul 2>nul
if not errorlevel 1 (
    set "PY_EXE=py"
    goto :FOUND_PYTHON
)
set "PY_EXE=python"

:FOUND_PYTHON
"!PY_EXE!" -c "import fastapi, uvicorn, jinja2, httpx, aiosqlite" >nul 2>nul
if errorlevel 1 (
    echo.
    echo [*] Resolving missing dependencies in Python runtime...
    "!PY_EXE!" -m pip install fastapi uvicorn jinja2 httpx aiosqlite python-multipart itsdangerous cryptography bcrypt pydantic --no-warn-script-location
)

:MENU
cls
echo ================================================================================
echo   JOBHUNT PRO SAAS - 24/7 AUTONOMOUS SOVEREIGN ENGINE
echo ================================================================================
echo   [*] Root Workspace  : "!ROOT_DIR!"
echo   [*] Python Runtime  : "!PY_EXE!"
echo   [*] Main Platform   : http://127.0.0.1:!PORT!
echo   [*] Instant Login   : http://127.0.0.1:!PORT!/auth/instant-login
echo   [*] User Dashboard  : http://127.0.0.1:!PORT!/user-dashboard
echo   [*] Sent Emails Log : http://127.0.0.1:!PORT!/sent-emails
echo   [*] Battle Station  : http://127.0.0.1:!PORT!/battle-station
echo   [*] Free ATS Magnet : http://127.0.0.1:!PORT!/free-ats-score
echo   [*] Reseller Matrix : http://127.0.0.1:!PORT!/reseller
echo   [*] Sovereign Store : http://127.0.0.1:!PORT!/store
echo   [*] Sovereign Wallet: http://127.0.0.1:!PORT!/wallet
echo   [*] Admin Control   : http://127.0.0.1:!PORT!/admin
echo ================================================================================
echo.
echo   [1] Start 24/7 Sovereign Production Server + Swarm (Default - Auto in 2s)
echo   [2] Start Hot-Reload Development Engine (--dev)
echo   [3] Start Standalone 24/7 AI Dispatcher Streaming Console
echo   [4] Open Instant Zero-Buffering Login in Browser
echo   [5] Run Full Automated Diagnostic ^& Integration Test Suite
echo   [6] Open Encrypted Database Backup Vault
echo   [7] Force Port Reset ^& Clear Stale Temp Locks
echo.
echo ================================================================================

choice /c 1234567 /t 2 /d 1 /n /m " Select an option [1-7] or wait for instant auto-start: "
set "SEL=%ERRORLEVEL%"

if "%SEL%"=="1" goto :START_PROD
if "%SEL%"=="2" goto :START_DEV
if "%SEL%"=="3" goto :START_DAEMON
if "%SEL%"=="4" goto :OPEN_DIRECT_LOGIN
if "%SEL%"=="5" goto :RUN_TESTS
if "%SEL%"=="6" goto :OPEN_VAULT
if "%SEL%"=="7" goto :RESET_PORTS

:START_DAEMON
cls
echo [*] Launching 24/7 Autonomous AI Dispatcher Console...
start "" "!ROOT_DIR!\start_dispatcher_daemon.bat"
goto :MENU

:START_PROD
echo.
echo [*] Launching High-Performance Sovereign Engine ^& AI Swarms on port !PORT!...
echo.
"!PY_EXE!" "!ROOT_DIR!\run_local_server.py" --port !PORT!
goto :SERVER_EXIT

:START_DEV
echo.
echo [*] Launching Development Engine with Hot-Reload on port !PORT!...
echo.
"!PY_EXE!" "!ROOT_DIR!\run_local_server.py" --port !PORT! --dev
goto :SERVER_EXIT

:OPEN_DIRECT_LOGIN
echo.
echo [*] Opening Instant Zero-Buffering Login in Browser...
start "" "http://127.0.0.1:!PORT!/auth/instant-login"
goto :MENU

:RUN_TESTS
cls
echo ================================================================================
echo   RUNNING FULL AUTOMATED VERIFICATION TEST SUITE
echo ================================================================================
"!PY_EXE!" -m pytest tests/test_multi_tenant_user_isolation.py tests/test_multi_cv_and_multi_tenant_matrix.py tests/e2e/test_r2_dashboard.py tests/test_emperor_dashboard.py tests/test_sovereign_reseller_engine.py -v
echo.
echo Press any key to return to menu...
pause >nul
goto :MENU

:OPEN_VAULT
explorer "%ROOT_DIR%\data\backups"
goto :MENU

:RESET_PORTS
echo.
echo [*] Force-terminating all lingering processes on port 8000, 8001, 8080...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8000 .*LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8001 .*LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8080 .*LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>nul
del /f /q "%TEMP%\jobhunt_*.lock" >nul 2>nul
echo [v] Port reset complete!
timeout /t 1 >nul
goto :MENU

:SERVER_EXIT
if errorlevel 1 (
    echo.
    echo ================================================================================
    echo   [!] Server stopped with exit code %ERRORLEVEL%.
    echo ================================================================================
    echo.
    echo   [1] Restart server immediately
    echo   [2] Return to menu
    echo   [3] Exit
    choice /c 123 /t 5 /d 1 /n /m " Auto-restarting in 5s or choose [1/2/3]: "
    if "!ERRORLEVEL!"=="1" goto :START_PROD
    if "!ERRORLEVEL!"=="2" goto :MENU
    if "!ERRORLEVEL!"=="3" exit /b 0
)

exit /b 0