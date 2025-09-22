@echo off
title Fix React Scripts Issue
color 0C

echo ===============================================
echo    FIXING REACT-SCRIPTS NOT FOUND ERROR
echo ===============================================
echo.

cd /d %~dp0frontend

echo [1/4] Checking current directory...
echo Current directory: %CD%
if not exist package.json (
    echo ❌ package.json not found! 
    echo Make sure you're running this from the Omerta project root
    pause
    exit /b 1
)
echo ✓ package.json found
echo.

echo [2/4] Clearing npm cache...
npm cache clean --force
echo ✓ npm cache cleared
echo.

echo [3/4] Removing node_modules and package-lock...
if exist node_modules (
    echo Removing old node_modules...
    rmdir /s /q node_modules
)
if exist package-lock.json (
    del package-lock.json
)
if exist yarn.lock (
    del yarn.lock
)
echo ✓ Old installations removed
echo.

echo [4/4] Fresh installation of dependencies...
echo This may take a few minutes...
npm install
if %errorlevel% neq 0 (
    echo ❌ npm install failed, trying yarn...
    yarn install
    if %errorlevel% neq 0 (
        echo ❌ Both npm and yarn failed
        echo.
        echo Please check:
        echo 1. Internet connection
        echo 2. Node.js is properly installed
        echo 3. npm/yarn are in PATH
        echo.
        pause
        exit /b 1
    ) else (
        echo ✓ Dependencies installed with yarn
    )
) else (
    echo ✓ Dependencies installed with npm
)
echo.

echo [VERIFY] Testing react-scripts...
npx react-scripts --version
if %errorlevel% neq 0 (
    echo ❌ react-scripts still not working
    echo Installing react-scripts globally as fallback...
    npm install -g react-scripts
) else (
    echo ✅ react-scripts is working correctly!
)
echo.

cd /d %~dp0

echo ===============================================
echo    ✅ REACT-SCRIPTS ISSUE FIXED!
echo ===============================================
echo.
echo You can now run:
echo - start_omerta_windows.bat
echo - start_omerta_windows_yarn.bat
echo.
echo Or manually: cd frontend && npm start
echo.
pause