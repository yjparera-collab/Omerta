# Omerta Intelligence Dashboard - PowerShell Startup Script
Write-Host "===============================================" -ForegroundColor Green
Write-Host "   OMERTA INTELLIGENCE DASHBOARD" -ForegroundColor Yellow
Write-Host "   Windows PowerShell Startup Script v2.0" -ForegroundColor Yellow  
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

# Set environment variables for this session
$env:MONGO_URL="mongodb://localhost:27017"
$env:DB_NAME="omerta_intelligence"
$env:CORS_ORIGINS="http://localhost:3000"

Write-Host "[1/5] Setting up environment variables..." -ForegroundColor Cyan
Write-Host "✓ MONGO_URL: $env:MONGO_URL" -ForegroundColor Green
Write-Host "✓ DB_NAME: $env:DB_NAME" -ForegroundColor Green
Write-Host "✓ CORS_ORIGINS: $env:CORS_ORIGINS" -ForegroundColor Green
Write-Host ""

Write-Host "[2/5] Checking MongoDB..." -ForegroundColor Cyan
Start-Sleep 2
try {
    Start-Service MongoDB -ErrorAction Stop
    Write-Host "✓ MongoDB started successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠ MongoDB might already be running or failed to start" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "[3/5] Starting Backend API Server..." -ForegroundColor Cyan
Start-Sleep 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python intelligence_server.py" -WindowStyle Normal
Write-Host "✓ Backend starting on port 8001" -ForegroundColor Green
Write-Host ""

Write-Host "[4/5] Starting Scraping Service (Windows - Visible Browser)..." -ForegroundColor Cyan  
Start-Sleep 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; python mongodb_scraping_service_windows.py" -WindowStyle Normal
Write-Host "✓ Scraping service starting on port 5001 (VISIBLE browser)" -ForegroundColor Green
Write-Host ""

Write-Host "[5/5] Starting Frontend..." -ForegroundColor Cyan
Start-Sleep 5
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm start" -WindowStyle Normal
Write-Host "✓ Frontend starting on port 3000" -ForegroundColor Green
Write-Host ""

Write-Host "===============================================" -ForegroundColor Green
Write-Host "   🎯 OMERTA INTELLIGENCE DASHBOARD" -ForegroundColor Yellow
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Dashboard URL: http://localhost:3000" -ForegroundColor White
Write-Host "🔗 Backend API:   http://localhost:8001/docs" -ForegroundColor White
Write-Host "🕷️  Scraper API:   http://localhost:5001/api/scraping/status" -ForegroundColor White
Write-Host "💾 MongoDB:       mongodb://localhost:27017" -ForegroundColor White
Write-Host ""
Write-Host "ℹ️  All services are starting in separate windows" -ForegroundColor Cyan
Write-Host "⚠️  Wait 30-60 seconds for full initialization" -ForegroundColor Yellow
Write-Host "🛑 Press any key to exit this monitor" -ForegroundColor Red
Write-Host ""

Read-Host "Press Enter to continue"