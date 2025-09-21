@echo off
title Omerta Intelligence Dashboard - Startup
color 0A

echo ===============================================
echo    OMERTA INTELLIGENCE DASHBOARD
echo    Windows Startup Script v2.0
echo ===============================================
echo.

echo [1/5] Checking MongoDB...
timeout 2 >nul
net start MongoDB >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ MongoDB started successfully
) else (
    echo ⚠ MongoDB might already be running or failed to start
)
echo.

echo [2/5] Starting Backend API Server...
timeout 2 >nul
start "Omerta Backend" cmd /k "title Omerta Backend API && cd /d %~dp0backend && python intelligence_server.py"
echo ✓ Backend starting on port 8001
echo.

echo [3/5] Starting Scraping Service...
timeout 3 >nul
start "Omerta Scraper" cmd /k "title Omerta Scraping Service && cd /d %~dp0 && python mongodb_scraping_service.py"
echo ✓ Scraping service starting on port 5001
echo.

echo [4/5] Starting Frontend...
timeout 5 >nul
start "Omerta Frontend" cmd /k "title Omerta Frontend && cd /d %~dp0frontend && yarn start"
echo ✓ Frontend starting on port 3000
echo.

echo [5/5] Services are starting up...
timeout 5 >nul

echo ===============================================
echo    🎯 OMERTA INTELLIGENCE DASHBOARD
echo ===============================================
echo.
echo 📊 Dashboard URL: http://localhost:3000
echo 🔗 Backend API:   http://localhost:8001/docs  
echo 🕷️  Scraper API:   http://localhost:5001/api/scraping/status
echo 💾 MongoDB:       mongodb://localhost:27017
echo.
echo ℹ️  All services are starting in separate windows
echo ⚠️  Wait 30-60 seconds for full initialization
echo 🛑 Close this window to stop monitoring
echo.

:monitor
timeout 10 >nul
echo [%time%] Services running... (Press Ctrl+C to exit)
goto monitor