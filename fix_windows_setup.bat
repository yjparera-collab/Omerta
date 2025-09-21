@echo off
title Omerta - Windows Setup Fixer
color 0E

echo ===============================================
echo    OMERTA WINDOWS SETUP TROUBLESHOOTER
echo ===============================================
echo.

echo [1/4] Checking .env file...
if exist "backend\.env" (
    echo ✓ .env file exists
    echo Inhoud van .env:
    type "backend\.env"
    echo.
    echo ⚠ Controleer of er GEEN spaties staan na de waarden!
) else (
    echo ❌ .env file niet gevonden!
    echo Maken van .env file...
    echo MONGO_URL=mongodb://localhost:27017> backend\.env
    echo DB_NAME=omerta_intelligence>> backend\.env
    echo CORS_ORIGINS=http://localhost:3000>> backend\.env
    echo ✓ .env file aangemaakt
)
echo.

echo [2/4] Checking MongoDB...
timeout 2 >nul
sc query MongoDB >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ MongoDB service gevonden
    net start MongoDB >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✓ MongoDB gestart
    ) else (
        echo ⚠ MongoDB draait mogelijk al
    )
) else (
    echo ❌ MongoDB service niet gevonden!
    echo.
    echo INSTALLATIE INSTRUCTIES:
    echo 1. Download MongoDB Community Server van:
    echo    https://www.mongodb.com/try/download/community
    echo 2. Installeer met standaard instellingen
    echo 3. Start deze script opnieuw
    echo.
    pause
    exit /b 1
)
echo.

echo [3/4] Checking Node.js en package managers...
node --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Node.js is geïnstalleerd
    node --version
) else (
    echo ❌ Node.js niet gevonden!
    echo Download van: https://nodejs.org/
    pause
    exit /b 1
)

npm --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ NPM is beschikbaar
    npm --version
) else (
    echo ❌ NPM niet gevonden!
)

yarn --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Yarn is beschikbaar
    yarn --version
) else (
    echo ⚠ Yarn niet gevonden - we gebruiken NPM
    echo Installeren van yarn (optioneel):
    echo npm install -g yarn
)
echo.

echo [4/4] Installing frontend dependencies...
cd frontend
if exist "yarn.lock" (
    if exist "node_modules" (
        echo ✓ Dependencies al geïnstalleerd
    ) else (
        echo Installing met NPM...
        npm install
        if %errorlevel% equ 0 (
            echo ✓ Frontend dependencies geïnstalleerd
        ) else (
            echo ❌ Fout bij installeren dependencies
        )
    )
) else (
    echo Installing met NPM...
    npm install
)
cd ..
echo.

echo ===============================================
echo    SETUP CONTROLE COMPLEET
echo ===============================================
echo.
echo Nu kun je starten met:
echo 1. start_omerta_windows.bat (automatisch)
echo 2. Of handmatig in 3 aparte terminals:
echo    - cd backend ^&^& python intelligence_server.py
echo    - python mongodb_scraping_service_windows.py  
echo    - cd frontend ^&^& npm start
echo.
pause