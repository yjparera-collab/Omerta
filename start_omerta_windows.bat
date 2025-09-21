@echo off
setlocal EnableExtensions EnableDelayedExpansion
color 0A
title Omerta Intelligence Dashboard - Startup

pushd %~dp0

echo ===============================================
echo    OMERTA INTELLIGENCE DASHBOARD
echo    Windows CMD Startup Script v2.1 (safe env)
echo ===============================================
echo.

echo [1/5] Environment sanity...
rem Clear in-session vars to avoid polluted values
set MONGO_URL=
set DB_NAME=
set CORS_ORIGINS=
echo ✓ Cleared session variables


echo [2/5] Checking MongoDB service (optional)...
timeout 2 >nul
net start MongoDB >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ MongoDB started successfully
) else (
    echo ⚠ MongoDB might already be running or failed to start
)
echo.

echo [3/5] Starting Backend API Server...
timeout 2 >nul
start "Omerta Backend" cmd /k "title Omerta Backend API && cd /d %~dp0backend && setlocal EnableExtensions EnableDelayedExpansion && set "MONGO_URL=mongodb://127.0.0.1:27017" && set "DB_NAME=omerta_intelligence" && set "CORS_ORIGINS=http://localhost:3000" && echo Using MONGO_URL=[!MONGO_URL!] && python intelligence_server.py"
echo ✓ Backend starting on port 8001
echo.

echo [4/5] Starting Scraping Service (Windows - Visible Browser)...
timeout 3 >nul
start "Omerta Scraper" cmd /k "title Omerta Scraping Service && cd /d %~dp0 && setlocal EnableExtensions EnableDelayedExpansion && set "MONGO_URL=mongodb://127.0.0.1:27017" && set "DB_NAME=omerta_intelligence" && echo Using MONGO_URL=[!MONGO_URL!] && python mongodb_scraping_service_windows.py"
echo ✓ Scraping service starting on port 5001 (VISIBLE browser for Cloudflare)
echo.

echo [5/5] Starting Frontend...
timeout 5 >nul
start "Omerta Frontend" cmd /k "title Omerta Frontend && cd /d %~dp0frontend && npm start"
echo ✓ Frontend starting on port 3000
echo.

echo [6/6] Services are starting up...
timeout 5 >nul

echo ===============================================
echo    🎯 OMERTA INTELLIGENCE DASHBOARD
echo ===============================================
echo.
echo 📊 Dashboard URL: http://localhost:3000
echo 🔗 Backend API:   http://localhost:8001/docs
set "_MONGO_PRINT=mongodb://127.0.0.1:27017"
echo 🕷️  Scraper API:   http://127.0.0.1:5001/api/scraping/status
echo 💾 MongoDB:       %_MONGO_PRINT%
set _MONGO_PRINT=
echo.
echo ℹ️  All services are starting in separate windows
echo ⚠️  Wait 30-60 seconds for full initialization
echo 🛑 Close this window to stop monitoring
echo.

:monitor
timeout 10 >nul
echo [%time%] Services running... (Press Ctrl+C to exit)
goto monitor

popd