#!/usr/bin/env python3
"""
Quick Windows Fix - Create missing Windows-specific files
"""

import os
from pathlib import Path

def create_missing_windows_files():
    """Create the missing Windows-specific startup files"""
    
    # Windows-compatible startup script
    start_script_content = '''#!/usr/bin/env python3
"""
Windows Startup Script for Omerta Intelligence Dashboard
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def main():
    print("=" * 60)
    print("[TARGET] OMERTA INTELLIGENCE DASHBOARD")
    print("=" * 60)
    
    # Check for required files
    required_files = ["scraping_service.py", "backend/intelligence_server.py"]
    missing_files = []
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("[ERROR] Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        print("\\nPlease ensure you have extracted the complete package.")
        return
    
    print("[START] Starting services...")
    
    try:
        # Start FastAPI backend
        print("\\n[START] Starting FastAPI server...")
        backend_process = subprocess.Popen([
            sys.executable, "backend/intelligence_server.py"
        ])
        time.sleep(3)
        
        # Start scraping service
        print("[START] Starting scraping service...")
        scraping_process = subprocess.Popen([
            sys.executable, "scraping_service.py"
        ])
        time.sleep(3)
        
        # Start frontend if available
        if os.path.exists("frontend/package.json"):
            print("[START] Starting React frontend...")
            frontend_process = subprocess.Popen([
                "npm", "start"
            ], cwd="frontend")
        
        print("\\n[SUCCESS] All services started!")
        print("\\nAccess points:")
        print("  • Dashboard: http://localhost:3000")
        print("  • API: http://localhost:8001")
        print("  • Scraping: http://localhost:5001")
        
        print("\\n[INFO] Press Ctrl+C to stop all services")
        
        # Keep running
        while True:
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\\n[STOP] Shutting down...")
        try:
            backend_process.terminate()
            scraping_process.terminate()
            if 'frontend_process' in locals():
                frontend_process.terminate()
        except:
            pass
        print("[OK] Services stopped.")
        
    except Exception as e:
        print(f"[ERROR] Failed to start: {e}")
        print("\\nTry running services manually:")
        print("  python backend/intelligence_server.py")
        print("  python scraping_service.py")

if __name__ == "__main__":
    main()
'''

    # Windows install script
    install_script_content = '''#!/usr/bin/env python3
"""
Simple Windows installer for Omerta Dashboard
"""

import subprocess
import sys
import os

def run_command(command, description):
    print(f"\\n[SETUP] {description}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"[OK] {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed")
        return False

def main():
    print("=" * 50)
    print("[SETUP] OMERTA DASHBOARD WINDOWS INSTALLER")  
    print("=" * 50)
    
    # Install Python packages
    if os.path.exists("backend/requirements.txt"):
        run_command("pip install -r backend/requirements.txt", "Installing Python packages")
    else:
        # Install essential packages
        packages = [
            "fastapi", "uvicorn", "motor", "python-dotenv",
            "aiohttp", "undetected-chromedriver", "beautifulsoup4", 
            "selenium", "flask"
        ]
        for pkg in packages:
            run_command(f"pip install {pkg}", f"Installing {pkg}")
    
    # Install frontend packages
    if os.path.exists("frontend"):
        os.chdir("frontend")
        if run_command("npm install --legacy-peer-deps", "Installing frontend (method 1)"):
            print("[OK] Frontend installed successfully")
        elif run_command("npm install --force", "Installing frontend (method 2)"):  
            print("[OK] Frontend force installed")
        else:
            print("[WARNING] Frontend install failed, dashboard may not work")
        os.chdir("..")
    
    print("\\n[SUCCESS] Installation complete!")
    print("\\nNext: python start_intelligence.py")

if __name__ == "__main__":
    main()
'''

    # Create the files
    with open("start_intelligence.py", "w") as f:
        f.write(start_script_content)
    
    with open("install_dependencies.py", "w") as f:
        f.write(install_script_content)
    
    print("Created missing Windows files:")
    print("  - start_intelligence.py")
    print("  - install_dependencies.py")
    print("\\nNow you can run:")
    print("  python install_dependencies.py")
    print("  python start_intelligence.py")

if __name__ == "__main__":
    create_missing_windows_files()