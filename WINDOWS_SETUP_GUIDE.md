# Windows Setup Guide for Omerta Intelligence Dashboard

## Prerequisites

1. **Python 3.11+** installed
2. **Node.js 18+** and **yarn** installed
3. **Chrome browser** installed
4. **MongoDB** running locally

## Step 1: Install MongoDB on Windows

### Option A: MongoDB Community Server
1. Download from: https://www.mongodb.com/try/download/community
2. Install with default settings
3. Start MongoDB service:
   ```bash
   net start MongoDB
   ```

### Option B: MongoDB with Docker
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

## Step 2: Setup Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `.env` file in `backend/` folder:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=omerta_intelligence
CORS_ORIGINS=http://localhost:3000
```

Start backend:
```bash
python intelligence_server.py
```

## Step 3: Setup Scraping Service

Install Chrome dependencies:
```bash
pip install undetected-chromedriver beautifulsoup4 pymongo
```

Start scraping service:
```bash
python mongodb_scraping_service.py
```

**IMPORTANT**: The scraping service MUST run on port 5001 for the backend to connect.

## Step 4: Setup Frontend

```bash
cd frontend
yarn install
```

Create `.env` file in `frontend/` folder:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=3000
```

Start frontend:
```bash
yarn start
```

## Step 5: Verify Setup

1. **Backend**: http://localhost:8001/docs
2. **Frontend**: http://localhost:3000  
3. **MongoDB**: Should be running on port 27017
4. **Scraping Service**: Should be running on port 5001

## Troubleshooting

### "Cannot connect to host localhost:5001"
- Make sure `mongodb_scraping_service.py` is running
- Check if port 5001 is blocked by firewall
- Verify Chrome is installed

### "404 Player Not Found"
- This is normal if no player data has been scraped yet
- Add some detective targets first via the Families page

### Chrome/ChromeDriver Issues
```bash
pip install --upgrade undetected-chromedriver
```

### MongoDB Connection Issues
- Check if MongoDB service is running: `net start MongoDB`
- Verify connection: `mongo --eval "db.adminCommand('ismaster')"`

## One-Click Startup Script

Create `start_omerta_windows.bat`:
```batch
@echo off
echo Starting Omerta Intelligence Dashboard...

start "MongoDB" cmd /k "net start MongoDB"
timeout 3

start "Backend" cmd /k "cd backend && python intelligence_server.py"
timeout 3

start "Scraping Service" cmd /k "python mongodb_scraping_service.py"  
timeout 5

start "Frontend" cmd /k "cd frontend && yarn start"

echo All services started!
echo Frontend: http://localhost:3000
pause
```

## Performance Tips

1. **Close unnecessary Chrome instances** before starting
2. **Add Windows Defender exclusions** for the project folder
3. **Run as Administrator** if you encounter permission issues
4. **Use MongoDB Compass** for database visualization

## Architecture Overview

```
Frontend (React :3000) 
    ↓ API calls
Backend (FastAPI :8001)
    ↓ Service calls  
Scraping Service (Flask :5001)
    ↓ Data storage
MongoDB (:27017)
```

All services must be running for full functionality.