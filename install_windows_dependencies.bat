@echo off
title Omerta Intelligence - Dependencies Installer
color 0A

echo ===============================================
echo    OMERTA INTELLIGENCE DASHBOARD
echo    Windows Dependencies Installer
echo ===============================================
echo.

echo [1/4] Checking Node.js and npm...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed!
    echo.
    echo Please install Node.js from: https://nodejs.org/
    echo Recommended version: 18.x or higher
    echo.
    pause
    exit /b 1
) else (
    echo ✓ Node.js found
    node --version
)

npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm is not available!
    echo Please reinstall Node.js from: https://nodejs.org/
    pause
    exit /b 1
) else (
    echo ✓ npm found
    npm --version
)
echo.

echo [2/4] Installing Backend Dependencies...
cd /d %~dp0backend
if exist requirements.txt (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Failed to install Python dependencies
        echo Please ensure Python and pip are installed
        pause
        exit /b 1
    ) else (
        echo ✓ Python dependencies installed
    )
) else (
    echo ❌ requirements.txt not found in backend folder
    pause
    exit /b 1
)
echo.

echo [3/4] Installing Frontend Dependencies...
cd /d %~dp0frontend
if exist package.json (
    echo Installing npm packages (this may take a few minutes)...
    npm install
    if %errorlevel% neq 0 (
        echo ❌ Failed to install npm dependencies
        echo.
        echo Trying to fix with npm cache clean...
        npm cache clean --force
        npm install
        if %errorlevel% neq 0 (
            echo ❌ Still failed. Please check your internet connection and try again.
            pause
            exit /b 1
        )
    )
    echo ✓ Frontend dependencies installed
) else (
    echo ❌ package.json not found in frontend folder
    pause
    exit /b 1
)
echo.

echo [4/4] Verifying Installation...
echo Checking if react-scripts is available...
npx react-scripts --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ react-scripts still not available
    echo Trying to install react-scripts globally...
    npm install -g react-scripts
) else (
    echo ✓ react-scripts is working
)
echo.

cd /d %~dp0

echo ===============================================
echo    ✅ INSTALLATION COMPLETE!
echo ===============================================
echo.
echo Next steps:
echo 1. Run: start_omerta_windows.bat
echo 2. Keep Chrome browser window open for Cloudflare bypass
echo 3. Solve CAPTCHAs when they appear
echo.
echo Troubleshooting:
echo - If frontend still fails: npm install in frontend folder
echo - If backend fails: pip install -r requirements.txt in backend folder
echo - For MongoDB issues: ensure MongoDB is running on localhost:27017
echo.
pause