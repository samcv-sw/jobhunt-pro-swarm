@echo off
title PROJECT KRONOS - MILLISECOND PROFIT ENGINES
color 0B

echo =========================================
echo ⏱️ PROJECT KRONOS: INITIALIZING...
echo =========================================
echo.

echo [1/3] Starting The API Cartel Gateway (RapidAPI)...
start "KRONOS: API Gateway" cmd /c "python rapidapi_gateway.py & pause"

echo [2/3] Spinning up The SEO Matrix...
start "KRONOS: SEO Generator" cmd /c "python seo_matrix_generator.py & pause"

echo [3/3] Mining Database for B2B Leads...
start "KRONOS: Data Broker" cmd /c "python data_broker_export.py & pause"

echo.
echo ✅ ALL KRONOS ENGINES IGNITED.
echo Check the new terminal windows for live logs.
pause
