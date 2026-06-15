@echo off
chcp 65001 >nul
echo ============================================
echo  JobHunt Pro - Telegram Bot Auto-Start Setup
echo ============================================
echo.

:: Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ This needs ADMIN rights to create scheduled task.
    echo Right-click this file → "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo Creating scheduled task: "JobHuntPro_TelegramBot"
echo Bot will auto-start when you log into Windows.

schtasks /create /tn "JobHuntPro_TelegramBot" ^
  /tr "C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe bot_watchdog.py" ^
  /sc onlogon ^
  /it ^
  /f ^
  /ru "samde"

if %errorlevel% equ 0 (
    echo.
    echo ✅ SUCCESS! Bot will auto-start on every login.
    echo    Task: JobHuntPro_TelegramBot
    echo    Script: bot_watchdog.py
    echo    Folder: C:\Users\samde\Desktop\cv sam new ma3 kimi\
) else (
    echo.
    echo ❌ Failed to create task. Trying alternative method...
    echo.
    echo Adding to Startup folder instead...
    
    :: Fallback: create shortcut in Startup folder
    set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
    set "VBS=%STARTUP%\JobHuntPro_Bot.vbs"
    
    echo Set WshShell = CreateObject("WScript.Shell") > "%VBS%"
    echo WshShell.Run """C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe"" bot_watchdog.py", 0, False >> "%VBS%"
    echo WshShell = Nothing >> "%VBS%"
    
    echo ✅ Created startup script: %VBS%
    echo    Bot will start hidden on next login.
)

echo.
echo ============================================
echo  To start bot NOW (without reboot):
echo    cd "C:\Users\samde\Desktop\cv sam new ma3 kimi"
echo    python bot_watchdog.py
echo ============================================
pause
