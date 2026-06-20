@echo off
title PROJECT MIDAS Engine
color 0A

echo =========================================
echo 💰 PROJECT MIDAS: THE MONEY PRINTER 💰
echo =========================================
echo.
echo Activating The Ghost Agency...
start "MIDAS: Ghost Agency" cmd /c "python ghost_agency.py & pause"

echo Activating The Freelance Swarm...
start "MIDAS: Freelance Swarm" cmd /c "python freelance_swarm.py & pause"

echo.
echo Both engines are now running in the background.
echo Check the new terminal windows for live updates.
echo Do not close this window if you want to stop them together (use Task Manager to kill Python if needed).
pause
