@echo off
title 🕷️ ZERO-TOUCH AUTONOMOUS MARKETING BOTNET
color 0A

echo ========================================================
echo        JobHunt Pro - Viral Marketing Botnet
echo ========================================================
echo.
echo [1] Initializing GitHub Scout...
echo [2] Initializing QCLAW Auto-Marketer...
echo.
echo This window will run indefinitely in the background.
echo Do not close this window if you want the botnet to run.
echo.

:loop
echo [%time%] 🕷️ Starting GitHub Lead Generation Cycle...
python lead_generator.py

echo [%time%] 📧 Starting Email Blast Cycle...
python auto_marketer.py

echo [%time%] 💤 Cycle Complete. Sleeping for 1 hour to avoid rate limits...
timeout /t 3600 /nobreak > nul
goto loop
