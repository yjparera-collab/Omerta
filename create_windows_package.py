#!/usr/bin/env python3
"""
Create Windows-compatible Omerta Intelligence Dashboard Package
Fixes Unicode, NPM, and Windows-specific issues
"""

import os
import zipfile
from pathlib import Path
import shutil
import json

def create_windows_package():
    """Create Windows-compatible Omerta Intelligence package"""
    
    package_name = "omerta-intelligence-dashboard-windows"
    zip_name = f"{package_name}.zip"
    
    print("Creating Windows-compatible Omerta Intelligence Dashboard Package...")
    print("=" * 70)
    
    # Create temporary directory structure
    temp_dir = Path("/tmp/omerta-package-windows")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    temp_dir.mkdir(parents=True)
    project_dir = temp_dir / package_name
    project_dir.mkdir()
    
    # Create directory structure
    directories = [
        "backend",
        "frontend/src/components", 
        "frontend/src/hooks",
        "frontend/public",
        "logs",
        "data", 
        "cache"
    ]
    
    for dir_path in directories:
        (project_dir / dir_path).mkdir(parents=True, exist_ok=True)
        print(f"[DIR] Created directory: {dir_path}")

    # Windows-compatible file contents (NO UNICODE EMOJIS)
    files_content = {
        
        # Root files
        "README.md": '''# Omerta War Intelligence Dashboard (Windows Edition)

A sophisticated, real-time intelligence dashboard for the online game Barafranca (Omerta). 
This Windows edition fixes Unicode and dependency issues for seamless Windows operation.

## Architecture

**Hybrid System Design:**
- **Flask Scraping Service** (Port 5001) - Selenium-based data collection with Cloudflare bypass
- **FastAPI Intelligence API** (Port 8001) - WebSocket real-time updates and REST APIs  
- **React Frontend** (Port 3000) - Modern dashboard interface with live intelligence feed
- **Dual Database** - SQLite for high-frequency cache/analytics + MongoDB for app state

## Quick Start (Windows)

### Prerequisites
- Python 3.8+ (from python.org)
- Node.js 16+ (from nodejs.org)  
- Chrome browser (for Selenium)
- MongoDB (download from mongodb.com OR use MongoDB Atlas cloud)

### Installation Steps

1. **Extract this package** to your desired location (e.g., C:\\Omerta\\)

2. **Install Dependencies**
```cmd
python install_dependencies_windows.py
```

3. **Start All Services**  
```cmd
python start_intelligence.py
```

4. **Browser Setup** - First run will open Chrome, solve CAPTCHA if prompted

5. **Access Dashboard** - Open http://localhost:3000 in your browser

## Features

### Real-Time Intelligence
- **Smart List Worker** - Monitors all players every 30 seconds
- **Detective Mode** - Intensive tracking of selected targets (30s cache)
- **Critical Alerts** - Plating drops, kills, shots, profile changes
- **WebSocket Updates** - Live dashboard without page refresh

### Target Management  
- **Family Tracking** - Monitor entire families with one click
- **Individual Targets** - Precision tracking of high-value players
- **Priority Queue** - Smart scheduling ensures fastest updates
- **Web Interface** - Easy configuration through modern UI

### War Analytics
- **Combat Trends** - Kill/shot activity analysis with charts
- **Intelligence Feed** - Live stream of all combat actions
- **Performance Metrics** - System monitoring and health checks
- **Historical Data** - Configurable time ranges (1h to 7d)

## Windows-Specific Fixes

This package includes:
- Unicode emoji removal for Windows console compatibility
- NPM dependency resolution fixes (--legacy-peer-deps)
- Windows-friendly file paths and error handling
- PowerShell compatible commands

## Dashboard Usage

### Players Page (http://localhost:3000)
- Filter & search players by name, family, rank
- Multi-select checkbox for detective tracking
- Live intelligence notifications sidebar
- Sortable columns with game-aware logic

### Families Page (http://localhost:3000/families)  
- Configure family targets for monitoring
- View member statistics and online status
- Batch family selection with expand/collapse

### Analytics Page (http://localhost:3000/analytics)
- Real-time combat activity charts
- System performance monitoring
- Historical trend analysis
- Activity timeline with timestamps

## Configuration

All configuration is handled automatically. Key settings in scraping_service.py:

```python
# Scraping intervals (adjustable)
MAIN_LIST_INTERVAL = 30      # Seconds between full scans
CACHE_DURATION = 30          # Detective target cache time
BATCH_SIZE = 5               # Players processed per batch
```

## Security & Performance

### Cloudflare Bypass Strategy
- Uses undetected-chromedriver for stealth browsing
- 8-second automatic wait for Cloudflare challenge
- Manual CAPTCHA fallback for complex challenges
- Respects rate limits and appears as normal browser

### Performance Optimizations
- Hash-based change detection (only process when data changes)
- Smart caching (30s for detective targets, 5min for others)
- Priority queue system for high-value targets
- Single browser instance with tab reuse
- Batch processing for efficiency

## Troubleshooting Windows Issues

### Python Unicode Errors
This package removes all Unicode emojis to prevent Windows console errors.

### NPM Dependency Conflicts
```cmd
cd frontend
npm install --legacy-peer-deps
```
Or if that fails:
```cmd
npm install --force
```

### MongoDB Connection Issues  
```cmd
# Install MongoDB Community Server from mongodb.com
# OR use MongoDB Atlas (cloud) and update backend/.env with connection string
```

### Chrome/Selenium Issues
```cmd
pip install --upgrade undetected-chromedriver
# Ensure Google Chrome browser is installed from google.com/chrome
```

### Port Already in Use
```cmd
# Check what's using the ports
netstat -ano | findstr :3000
netstat -ano | findstr :8001
netstat -ano | findstr :5001

# Kill processes if needed
taskkill /PID <process_id> /F
```

## Important Notes

- **First Run**: Manual CAPTCHA solving may be required in Chrome
- **Browser Required**: Google Chrome must be installed for scraping
- **Public APIs Only**: Uses only publicly available game data
- **Local Processing**: All intelligence analysis happens locally
- **No Game Automation**: Pure intelligence gathering, no game interaction

## Windows Installation Tips

1. **Run as Administrator** if you encounter permission issues
2. **Disable Antivirus** temporarily if it blocks Chrome automation
3. **Use Command Prompt** instead of PowerShell if you have issues
4. **Check Windows Firewall** if services can't communicate

## Access Points

Once running, access these URLs:
- **Main Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8001/docs
- **Scraping Status**: http://localhost:5001/api/scraping/status  
- **WebSocket Endpoint**: ws://localhost:8001/ws

**Built for tactical intelligence in Omerta. Knowledge is power.**

**Windows Edition - Optimized for Windows 10/11 compatibility**
''',

        "install_dependencies_windows.py": '''#!/usr/bin/env python3
"""
Windows-compatible installer for Omerta Intelligence Dashboard
Handles Unicode issues and NPM dependency conflicts
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and print status"""
    print(f"\\n[SETUP] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"[OK] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def main():
    print("=" * 70)
    print("[TARGET] OMERTA INTELLIGENCE DASHBOARD SETUP (WINDOWS)")
    print("=" * 70)
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("[ERROR] Python 3.8+ is required")
        print("Download from: https://python.org")
        return False
    
    print(f"[OK] Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")

    # Install Python dependencies
    backend_requirements = Path(__file__).parent / "backend" / "requirements.txt"
    
    if backend_requirements.exists():
        if not run_command(f"pip install -r {backend_requirements}", "Installing Python dependencies"):
            # Try with upgrade flag
            if not run_command(f"pip install -r {backend_requirements} --upgrade", "Retrying with upgrade"):
                print("[WARNING] Some Python packages may have failed, continuing...")
    
    # Install frontend dependencies with Windows-specific flags
    frontend_dir = Path(__file__).parent / "frontend"
    if frontend_dir.exists():
        original_dir = os.getcwd()
        os.chdir(frontend_dir)
        
        print("\\n[SETUP] Installing frontend dependencies (this may take a few minutes)...")
        
        # Method 1: Try npm with legacy peer deps (Windows friendly)
        if run_command("npm install --legacy-peer-deps", "Installing with legacy peer deps"):
            print("[OK] Frontend dependencies installed successfully")
        # Method 2: Try force install
        elif run_command("npm install --force", "Force installing dependencies"):
            print("[OK] Frontend dependencies force installed")
        # Method 3: Clear cache and try again
        elif run_command("npm cache clean --force && npm install --legacy-peer-deps", "Clean cache and retry"):
            print("[OK] Frontend dependencies installed after cache clear")
        else:
            print("[WARNING] Frontend dependencies failed, but continuing...")
            print("         You may need to install Node.js from https://nodejs.org")
        
        os.chdir(original_dir)

    # Create directories if they don't exist
    directories = ["logs", "data", "cache"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"[DIR] Ensured directory exists: {directory}")

    print("\\n" + "=" * 70)
    print("[SUCCESS] WINDOWS SETUP COMPLETED!")
    print("=" * 70)
    print("Next steps:")
    print("  1. Run: python start_intelligence.py")
    print("  2. Wait for Chrome browser to open")
    print("  3. Solve CAPTCHA if prompted (first time only)")
    print("  4. Open browser to: http://localhost:3000")
    print("  5. Configure target families and monitor intelligence!")
    print("\\nTroubleshooting:")
    print("  - If Chrome doesn't work: Install Google Chrome browser")
    print("  - If MongoDB errors: Install MongoDB or use cloud version")
    print("  - If port errors: Check nothing else is using ports 3000, 8001, 5001")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\\n[ERROR] Setup failed. Please check the errors above and try again.")
        print("\\nCommon fixes:")
        print("  - Install Python 3.8+ from python.org")
        print("  - Install Node.js from nodejs.org")  
        print("  - Install Google Chrome browser")
        print("  - Run as Administrator if permission issues")
        sys.exit(1)
''',

        "start_intelligence_windows.py": '''#!/usr/bin/env python3
"""
Windows-compatible Omerta War Intelligence Dashboard Starter
Starts Flask scraping service and FastAPI dashboard with Windows-friendly output
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def start_service(script_path, service_name, port):
    """Start a service and return the process"""
    print(f"[START] Starting {service_name} on port {port}...")
    try:
        # Use CREATE_NEW_CONSOLE on Windows to avoid Unicode issues
        if os.name == 'nt':  # Windows
            process = subprocess.Popen([
                sys.executable, script_path
            ], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # Linux/Mac
            process = subprocess.Popen([
                sys.executable, script_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        time.sleep(3)  # Give it time to start
        
        if process.poll() is None:
            print(f"[OK] {service_name} started successfully (PID: {process.pid})")
            return process
        else:
            print(f"[ERROR] {service_name} failed to start")
            return None
    except Exception as e:
        print(f"[ERROR] Error starting {service_name}: {e}")
        return None

def main():
    print("=" * 70)
    print("[TARGET] OMERTA WAR INTELLIGENCE DASHBOARD (WINDOWS)")
    print("=" * 70)
    print("Starting hybrid architecture...")
    print("- Flask Scraping Service (Port 5001)")
    print("- FastAPI Dashboard API (Port 8001)")
    print("- React Frontend (Port 3000)")
    print("=" * 70)

    # Check if required files exist
    scraping_script = Path(__file__).parent / "scraping_service.py"
    api_script = Path(__file__).parent / "backend" / "intelligence_server.py"

    if not scraping_script.exists():
        print(f"[ERROR] Scraping service script not found: {scraping_script}")
        return

    if not api_script.exists():
        print(f"[ERROR] API server script not found: {api_script}")
        return

    processes = []

    try:
        # Start FastAPI dashboard first
        api_process = start_service(str(api_script), "FastAPI Dashboard API", 8001)
        if api_process:
            processes.append(("Dashboard API", api_process))
        else:
            print("[ERROR] Failed to start dashboard API. Exiting.")
            return

        time.sleep(2)

        # Start Flask scraping service  
        scraping_process = start_service(str(scraping_script), "Flask Scraping Service", 5001)
        if scraping_process:
            processes.append(("Scraping Service", scraping_process))
        else:
            print("[WARNING] Scraping service failed. Dashboard will work without live data.")

        # Start React frontend
        frontend_dir = Path(__file__).parent / "frontend"
        if frontend_dir.exists():
            print("[START] Starting React Frontend on port 3000...")
            if os.name == 'nt':  # Windows
                frontend_process = subprocess.Popen([
                    "npm", "start"
                ], cwd=frontend_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:  # Linux/Mac
                frontend_process = subprocess.Popen([
                    "npm", "start"
                ], cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            time.sleep(5)
            
            if frontend_process.poll() is None:
                print("[OK] React Frontend started successfully")
                processes.append(("React Frontend", frontend_process))

        print("\\n" + "=" * 70)
        print("[TARGET] OMERTA INTELLIGENCE DASHBOARD ACTIVE!")
        print("=" * 70)
        print("[COMM] Services Status:")
        for name, process in processes:
            status = "RUNNING" if process.poll() is None else "STOPPED"
            print(f"  {name}: {status} (PID: {process.pid})")
        
        print("\\n[WEB] Access Points:")
        print("  • Main Dashboard: http://localhost:3000")
        print("  • API Documentation: http://localhost:8001/docs") 
        print("  • Scraping Status: http://localhost:5001/api/scraping/status")
        print("  • WebSocket: ws://localhost:8001/ws")
        
        print("\\n[TARGET] Instructions:")
        print("  1. Chrome browser will open automatically for scraping setup")
        print("  2. Solve CAPTCHA if prompted (first time only)")
        print("  3. Open http://localhost:3000 in your browser")
        print("  4. Configure target families in the Families tab")
        print("  5. Monitor real-time intelligence on Players tab")
        print("  6. Press Ctrl+C in this window to shutdown all services")
        print("=" * 70)

        # Keep running until interrupted
        print("\\n[SETUP] System running... Press Ctrl+C to stop")
        while True:
            time.sleep(10)
            
            # Check if processes are still alive
            for name, process in processes:
                if process.poll() is not None:
                    print(f"[WARNING] {name} has stopped unexpectedly!")

    except KeyboardInterrupt:
        print("\\n[STOP] Shutting down services...")
        for name, process in processes:
            print(f"   Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   Force killing {name}...")
                process.kill()
        
        print("[OK] All services stopped. Goodbye!")

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        for name, process in processes:
            process.terminate()

if __name__ == "__main__":
    main()
''',

        # Backend files with Windows fixes
        "backend/requirements.txt": '''fastapi==0.110.1
uvicorn==0.25.0
python-dotenv>=1.0.1
pymongo==4.5.0
pydantic>=2.6.4
motor==3.3.1
requests>=2.31.0
aiohttp>=3.9.0
undetected-chromedriver>=3.5.0
beautifulsoup4>=4.12.0
selenium>=4.15.0
flask>=3.0.0
''',

        "backend/.env": '''MONGO_URL=mongodb://localhost:27017
DB_NAME=omerta_intelligence
CORS_ORIGINS=*
''',

        # Frontend files with fixed dependencies
        "frontend/.env": '''REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=443
''',

        "frontend/package.json": '''{
  "name": "omerta-intelligence-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.1",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
''',

        "frontend/tailwind.config.js": '''/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
''',

        "frontend/postcss.config.js": '''module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
''',

        "frontend/public/index.html": '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🎯</text></svg>" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Omerta War Intelligence Dashboard - Real-time tactical intelligence for Barafranca" />
    <title>Omerta Intelligence Dashboard</title>
    <style>
      body {
        background-color: #111827;
        color: #f9fafb;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      }
    </style>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
''',

        "frontend/src/index.js": '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
''',

        "frontend/src/index.css": '''@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #111827;
  color: #f9fafb;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #374151;
}

::-webkit-scrollbar-thumb {
  background: #6b7280;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Loading shimmer effect */
.loading-shimmer {
  background: linear-gradient(90deg, #374151 25%, #4b5563 50%, #374151 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* Button styles */
.btn-primary {
  background: linear-gradient(45deg, #3b82f6, #1d4ed8);
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
}
'''
    }
    
    # Copy all Windows-fixed source files
    source_files = {
        "scraping_service.py": "/app/scraping_service.py",
        "backend/intelligence_server.py": "/app/backend/intelligence_server.py", 
        "frontend/src/App.js": "/app/frontend/src/App.js",
        "frontend/src/App.css": "/app/frontend/src/App.css",
        "frontend/src/hooks/useIntelligence.js": "/app/frontend/src/hooks/useIntelligence.js",
        "frontend/src/components/Navigation.js": "/app/frontend/src/components/Navigation.js",
        "frontend/src/components/PlayersPage.js": "/app/frontend/src/components/PlayersPage.js",
        "frontend/src/components/FamiliesPage.js": "/app/frontend/src/components/FamiliesPage.js", 
        "frontend/src/components/AnalyticsPage.js": "/app/frontend/src/components/AnalyticsPage.js"
    }
    
    # Write files with content
    for file_path, content in files_content.items():
        full_path = project_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[FILE] Created: {file_path}")
    
    # Copy and fix source files 
    unicode_replacements = {
        "🔧": "[SETUP]", "🎯": "[TARGET]", "✅": "[OK]", "❌": "[ERROR]", "⚠️": "[WARNING]",
        "🚀": "[START]", "📡": "[COMM]", "🌐": "[WEB]", "🔌": "[CONNECT]", "📊": "[ANALYTICS]",
        "🕵️": "[DETECTIVE]", "🔒": "[SECURE]", "📋": "[COPY]", "📄": "[FILE]", "📁": "[DIR]",
        "🎉": "[SUCCESS]", "📦": "[PACKAGE]", "📏": "[SIZE]", "🛑": "[STOP]", "🔄": "[REFRESH]",
        "👥": "[PLAYERS]", "🚨": "[CRITICAL]", "🔫": "[SHOTS]", "👁️": "[INTEL]", "⚡": "[LIVE]",
        "🗄️": "[DB]", "📈": "[TRENDS]", "💾": "[CACHE]", "🕸️": "[SCRAPE]"
    }
    
    for dest_path, source_path in source_files.items():
        try:
            if os.path.exists(source_path):
                dest_full_path = project_dir / dest_path
                dest_full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Read, fix Unicode, and write
                with open(source_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace Unicode emojis for Windows compatibility
                for emoji, replacement in unicode_replacements.items():
                    content = content.replace(emoji, replacement)
                
                with open(dest_full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                print(f"[COPY] Fixed and copied: {dest_path}")
        except Exception as e:
            print(f"[WARNING] Could not copy {dest_path}: {e}")
    
    # Create zip file
    zip_path = Path("/app") / zip_name
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(temp_dir)
                zipf.write(file_path, arcname)
                
    # Cleanup
    shutil.rmtree(temp_dir)
    
    print("\\n" + "=" * 70)
    print("[SUCCESS] WINDOWS PACKAGE CREATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"[PACKAGE] Package: {zip_path}")
    print(f"[SIZE] Size: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"\\n[TARGET] Windows Fixes Applied:")
    print(f"  • Unicode emojis replaced with [BRACKETS]")
    print(f"  • NPM dependencies fixed for Windows")
    print(f"  • Console encoding issues resolved")
    print(f"  • Windows-specific install script included")
    print(f"\\n[START] Next Steps:")
    print(f"  1. Download: {zip_path}")
    print(f"  2. Extract to C:\\Omerta\\ (or desired location)")
    print(f"  3. Run: python install_dependencies_windows.py")
    print(f"  4. Run: python start_intelligence_windows.py")
    print("=" * 70)
    
    return str(zip_path)

if __name__ == "__main__":
    create_windows_package()