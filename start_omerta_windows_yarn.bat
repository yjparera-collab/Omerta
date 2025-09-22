@echo off
title Omerta Intelligence Dashboard - Startup (Yarn Version)
color 0A

echo ===============================================
echo    OMERTA INTELLIGENCE DASHBOARD
echo    Windows CMD Startup Script v2.2 (YARN)
echo ===============================================
echo.

echo [1/5] Setting up environment variables...
set "MONGO_URL=mongodb://localhost:27017"
set "DB_NAME=omerta_intelligence"
set "CORS_ORIGINS=http://localhost:3000"
set "BACKEND_URL=http://127.0.0.1:8001"
echo Using MONGO_URL=[%MONGO_URL%]
echo Using DB_NAME=[%DB_NAME%]
echo ✓ Environment variables set
echo.

echo [2/5] Checking MongoDB...
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
start "Omerta Backend" cmd /k "title Omerta Backend API && cd /d %~dp0backend && set "MONGO_URL=mongodb://localhost:27017" && set "DB_NAME=omerta_intelligence" && set "CORS_ORIGINS=http://localhost:3000" && python intelligence_server.py"
echo ✓ Backend starting on port 8001
echo.

echo [4/5] Starting Scraping Service (Windows - Visible Browser)...
timeout 3 >nul
start "Omerta Scraper" cmd /k "title Omerta Scraping Service && echo IMPORTANT: This window must stay OPEN for Cloudflare bypass && echo Solve any CAPTCHAs that appear in the Chrome browser && echo. && cd /d %~dp0 && set "MONGO_URL=mongodb://localhost:27017" && set "DB_NAME=omerta_intelligence" && set "BACKEND_URL=http://127.0.0.1:8001" && python mongodb_scraping_service_windows.py"
echo ✓ Scraping service starting on port 5001 (VISIBLE browser for Cloudflare)
echo.

echo [5/5] Starting Frontend with Yarn...
timeout 5 >nul
echo Checking if yarn dependencies are installed...
cd /d %~dp0frontend
if not exist node_modules (
    echo ❌ Frontend dependencies not found!
    echo Installing dependencies with yarn...
    yarn install
    if %errorlevel% neq 0 (
        echo ❌ Failed to install frontend dependencies with yarn
        echo Trying with npm...
        npm install
        if %errorlevel% neq 0 (
            echo ❌ Failed with both yarn and npm
            echo Please run: install_windows_dependencies.bat
            pause
            exit /b 1
        )
    )
)

echo Starting frontend with yarn...
start "Omerta Frontend" cmd /k "title Omerta Frontend && cd /d %~dp0frontend && yarn start"
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
echo 🕷️  Scraper API:   http://localhost:5001/api/scraping/status
echo 💾 MongoDB:       mongodb://localhost:27017
echo.
echo ℹ️  All services are starting in separate windows
echo ⚠️  Wait 30-60 seconds for full initialization
echo 🛑 Close this window to stop monitoring
echo.
echo 🔧 USERNAME-FIRST MODE: All data keyed by username
echo ✅ Using YARN for better dependency management
echo.
echo 🚨 TROUBLESHOOTING:
echo - If "react-scripts not found": run install_windows_dependencies.bat
echo - If yarn errors: install yarn globally with: npm install -g yarn
echo - If MongoDB errors: ensure MongoDB is running
echo - If Cloudflare issues: keep Chrome window open, solve CAPTCHAs
echo - If no player data: check scraping service logs for 403 errors
echo.

:monitor
timeout 10 >nul
echo [%time%] Services running... (Press Ctrl+C to exit)
goto monitor