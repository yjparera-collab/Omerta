#!/usr/bin/env python3
"""
Install all dependencies for Omerta Intelligence Dashboard
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and print status"""
    print(f"\n🔧 {description}...")
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
        
        if not run_command("yarn install", "Installing frontend dependencies"):
            print("⚠️ Yarn install failed, trying npm...")
            if not run_command("npm install", "Installing frontend dependencies with npm"):
                return False

    # Create necessary directories
    app_dir = Path(__file__).parent
    
    directories_to_create = [
        app_dir / "logs",
        app_dir / "data",
        app_dir / "cache"
    ]
    
    for directory in directories_to_create:
        directory.mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")

    print("\n" + "=" * 60)
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
        print("\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)