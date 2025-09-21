#!/usr/bin/env python3
"""
Omerta Intelligence Dashboard Package Creator
Creates a complete zip package for local installation
"""

import os
import zipfile
from pathlib import Path
import shutil

def create_omerta_package():
    """Create complete Omerta Intelligence package"""
    
    # Package info
    package_name = "omerta-intelligence-dashboard"
    zip_name = f"{package_name}.zip"
    
    print("🎯 Creating Omerta Intelligence Dashboard Package...")
    print("=" * 60)
    
    # Create temporary directory structure
    temp_dir = Path("/tmp/omerta-package")
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
        print(f"📁 Created directory: {dir_path}")

    # File contents
    files_content = {
        
        # Root files
        "README.md": '''# 🎯 Omerta War Intelligence Dashboard

A sophisticated, real-time intelligence dashboard for the online game Barafranca (Omerta). This application transforms raw public API data into actionable tactical intelligence during intense endgame scenarios.

## 🏗️ Architecture

**Hybrid System Design:**
- **Flask Scraping Service** (Port 5001) - Handles Selenium-based data collection with Cloudflare bypass
- **FastAPI Intelligence API** (Port 8001) - Provides WebSocket real-time updates and REST APIs  
- **React Frontend** (Port 3000) - Modern dashboard interface with live intelligence feed
- **Dual Database** - SQLite for high-frequency cache/analytics + MongoDB for app state

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Chrome browser (for Selenium)
- MongoDB (local or remote)

### Installation

1. **Install Dependencies**
```bash
python install_dependencies.py
```

2. **Start All Services**  
```bash
python start_intelligence.py
```

3. **Browser Setup** - Solve CAPTCHA if prompted on first run
4. **Configure Targets** - Navigate to http://localhost:3000/families
5. **Monitor Intelligence** - Watch real-time feed on Players dashboard

## 🎮 Features

### 📡 Real-Time Intelligence
- **Smart List Worker** - Monitors all players every 30 seconds
- **Detective Mode** - Intensive tracking of selected targets (30s cache)
- **Critical Alerts** - Plating drops, kills, shots, profile changes
- **WebSocket Updates** - Live dashboard without refresh

### 🎯 Target Management  
- **Family Tracking** - Monitor entire families
- **Individual Targets** - Precision tracking of high-value players
- **Priority Queue** - Smart scheduling for fastest updates
- **Web Interface** - Easy configuration through modern UI

### 📊 War Analytics
- **Combat Trends** - Kill/shot activity analysis
- **Intelligence Feed** - Live stream of all actions
- **Performance Metrics** - System monitoring
- **Historical Data** - Configurable time ranges

## 🔧 Configuration

All configuration is handled automatically. Key settings:

```python
# Scraping intervals
MAIN_LIST_INTERVAL = 30      # Seconds between scans
CACHE_DURATION = 30          # Detective target cache time
BATCH_SIZE = 5               # Players per batch
```

## 📊 Dashboard Usage

### Players Page (http://localhost:3000)
- Filter & search players by name, family, rank
- Multi-select for detective tracking
- Live intelligence notifications
- Sortable columns with game-aware logic

### Families Page (http://localhost:3000/families)  
- Configure family targets for monitoring
- View member statistics and status
- Batch family selection

### Analytics Page (http://localhost:3000/analytics)
- Real-time combat activity charts
- System performance monitoring
- Historical trend analysis

## 🛡️ Security & Performance

### Cloudflare Bypass
- Uses undetected-chromedriver
- 8-second automatic wait
- Manual CAPTCHA fallback
- Respects rate limits

### Optimizations
- Hash-based change detection
- Smart caching (30s-5min)
- Priority queue system
- Single browser instance
- Batch processing

## ⚠️ Important Notes

- **First Run**: Manual CAPTCHA solving may be required
- **Browser Required**: Chrome must be installed for scraping
- **Public APIs Only**: Uses only public game data
- **Local Processing**: All analysis happens locally

## 🔧 Troubleshooting

### Chrome Issues
```bash
pip install --upgrade undetected-chromedriver
# Ensure Chrome browser is installed
```

### MongoDB Issues  
```bash
# Start MongoDB
sudo systemctl start mongod  # Linux
brew services start mongodb-community  # Mac
net start MongoDB  # Windows
```

### Port Conflicts
```bash
# Check ports
netstat -tlnp | grep :3000
netstat -tlnp | grep :8001
netstat -tlnp | grep :5001
```

**Built for tactical intelligence in Omerta. Knowledge is power. 🎯**
''',

        "install_dependencies.py": '''#!/usr/bin/env python3
"""
Install all dependencies for Omerta Intelligence Dashboard
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and print status"""
    print(f"\\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def main():
    print("=" * 60)
    print("🎯 OMERTA INTELLIGENCE DASHBOARD SETUP")
    print("=" * 60)
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")

    # Install Python dependencies
    backend_requirements = Path(__file__).parent / "backend" / "requirements.txt"
    
    if backend_requirements.exists():
        if not run_command(f"pip install -r {backend_requirements}", "Installing Python dependencies"):
            return False
    else:
        print("⚠️ Backend requirements.txt not found, installing essential packages...")
        essential_packages = [
            "fastapi==0.110.1",
            "uvicorn==0.25.0", 
            "motor==3.3.1",
            "python-dotenv>=1.0.1",
            "aiohttp>=3.9.0",
            "undetected-chromedriver>=3.5.0",
            "beautifulsoup4>=4.12.0",
            "selenium>=4.15.0",
            "flask>=3.0.0"
        ]
        
        for package in essential_packages:
            if not run_command(f"pip install {package}", f"Installing {package}"):
                print(f"⚠️ Failed to install {package}, continuing...")

    # Install frontend dependencies
    frontend_dir = Path(__file__).parent / "frontend"
    if frontend_dir.exists():
        os.chdir(frontend_dir)
        
        if not run_command("npm install", "Installing frontend dependencies"):
            print("⚠️ npm install failed, trying yarn...")
            if not run_command("yarn install", "Installing frontend dependencies with yarn"):
                return False

    print("\\n" + "=" * 60)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("Next steps:")
    print("  1. Run: python start_intelligence.py")
    print("  2. Wait for Chrome browser setup (manual CAPTCHA may be required)")
    print("  3. Open browser to: http://localhost:3000")
    print("  4. Configure target families and enjoy real-time intelligence!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)
''',

        "start_intelligence.py": '''#!/usr/bin/env python3
"""
Omerta War Intelligence Dashboard Starter
Starts both Flask scraping service and FastAPI dashboard
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def start_service(script_path, service_name, port):
    """Start a service and return the process"""
    print(f"🚀 Starting {service_name} on port {port}...")
    try:
        process = subprocess.Popen([
            sys.executable, script_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(3)  # Give it time to start
        
        if process.poll() is None:
            print(f"✅ {service_name} started successfully (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ {service_name} failed to start:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return None
    except Exception as e:
        print(f"❌ Error starting {service_name}: {e}")
        return None

def main():
    print("=" * 60)
    print("🎯 OMERTA WAR INTELLIGENCE DASHBOARD")
    print("=" * 60)
    print("Starting hybrid architecture...")
    print("- Flask Scraping Service (Port 5001)")
    print("- FastAPI Dashboard API (Port 8001)")
    print("- React Frontend (Port 3000)")
    print("=" * 60)

    # Check if required files exist
    scraping_script = Path(__file__).parent / "scraping_service.py"
    api_script = Path(__file__).parent / "backend" / "intelligence_server.py"

    if not scraping_script.exists():
        print(f"❌ Scraping service script not found: {scraping_script}")
        return

    if not api_script.exists():
        print(f"❌ API server script not found: {api_script}")
        return

    processes = []

    try:
        # Start FastAPI dashboard first
        api_process = start_service(str(api_script), "FastAPI Dashboard API", 8001)
        if api_process:
            processes.append(("Dashboard API", api_process))
        else:
            print("❌ Failed to start dashboard API. Exiting.")
            return

        time.sleep(2)

        # Start Flask scraping service
        scraping_process = start_service(str(scraping_script), "Flask Scraping Service", 5001)
        if scraping_process:
            processes.append(("Scraping Service", scraping_process))
        else:
            print("⚠️ Scraping service failed to start. Dashboard will work without live data.")

        # Start React frontend
        frontend_dir = Path(__file__).parent / "frontend"
        if frontend_dir.exists():
            print("🚀 Starting React Frontend on port 3000...")
            frontend_process = subprocess.Popen([
                "npm", "start"
            ], cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time.sleep(5)
            
            if frontend_process.poll() is None:
                print("✅ React Frontend started successfully")
                processes.append(("React Frontend", frontend_process))

        print("\\n" + "=" * 60)
        print("🎯 OMERTA INTELLIGENCE DASHBOARD ACTIVE!")
        print("=" * 60)
        print("📡 Services Status:")
        for name, process in processes:
            status = "RUNNING" if process.poll() is None else "STOPPED"
            print(f"  {name}: {status} (PID: {process.pid})")
        
        print("\\n🌐 Access Points:")
        print("  • Main Dashboard: http://localhost:3000")
        print("  • API Documentation: http://localhost:8001/docs")
        print("  • Scraping Status: http://localhost:5001/api/scraping/status")
        print("  • WebSocket: ws://localhost:8001/ws")
        
        print("\\n📋 Instructions:")
        print("  1. Open your browser to: http://localhost:3000")
        print("  2. Configure target families in the Families tab")
        print("  3. Monitor real-time intelligence feed")
        print("  4. Press Ctrl+C to shutdown all services")
        print("=" * 60)

        # Keep running until interrupted
        while True:
            time.sleep(10)
            
            # Check if processes are still alive
            for name, process in processes:
                if process.poll() is not None:
                    print(f"⚠️  {name} has stopped unexpectedly!")

    except KeyboardInterrupt:
        print("\\n🛑 Shutting down services...")
        for name, process in processes:
            print(f"   Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   Force killing {name}...")
                process.kill()
        
        print("✅ All services stopped. Goodbye!")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        for name, process in processes:
            process.terminate()

if __name__ == "__main__":
    main()
''',

        # Backend files
        "backend/requirements.txt": '''fastapi==0.110.1
uvicorn==0.25.0
boto3>=1.34.129
requests-oauthlib>=2.0.0
cryptography>=42.0.8
python-dotenv>=1.0.1
pymongo==4.5.0
pydantic>=2.6.4
email-validator>=2.2.0
pyjwt>=2.10.1
passlib>=1.7.4
tzdata>=2024.2
motor==3.3.1
pytest>=8.0.0
black>=24.1.1
isort>=5.13.2
flake8>=7.0.0
mypy>=1.8.0
python-jose>=3.3.0
requests>=2.31.0
pandas>=2.2.0
numpy>=1.26.0
python-multipart>=0.0.9
jq>=1.6.0
typer>=0.9.0
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

        # Frontend files  
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
    "react-scripts": "5.0.1",
    "axios": "^1.6.0"
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
    <title>🎯 Omerta Intelligence</title>
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
'''
    }
    
    # Copy all source files from current app
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
        print(f"📄 Created: {file_path}")
    
    # Copy source files 
    for dest_path, source_path in source_files.items():
        try:
            if os.path.exists(source_path):
                dest_full_path = project_dir / dest_path
                dest_full_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_full_path)
                print(f"📋 Copied: {dest_path}")
        except Exception as e:
            print(f"⚠️ Could not copy {dest_path}: {e}")
    
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
    
    print("\\n" + "=" * 60)
    print("🎉 PACKAGE CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📦 Package: {zip_path}")
    print(f"📏 Size: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"\\n🚀 Next Steps:")
    print(f"  1. Download: {zip_path}")
    print(f"  2. Extract to your desired location")
    print(f"  3. Run: python install_dependencies.py")
    print(f"  4. Run: python start_intelligence.py")
    print("=" * 60)
    
    return str(zip_path)

if __name__ == "__main__":
    create_omerta_package()