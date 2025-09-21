#!/usr/bin/env python3
"""
Windows-compatible installer for Omerta Intelligence Dashboard
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and print status"""
    print(f"\n[SETUP] {description}...")
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
    print("=" * 60)
    print("[TARGET] OMERTA INTELLIGENCE DASHBOARD SETUP")
    print("=" * 60)
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("[ERROR] Python 3.8+ is required")
        return False
    
    print(f"[OK] Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")

    # Install Python dependencies
    backend_requirements = Path(__file__).parent / "backend" / "requirements.txt"
    
    if backend_requirements.exists():
        if not run_command(f"pip install -r {backend_requirements}", "Installing Python dependencies"):
            return False
    
    # Install frontend dependencies with npm and legacy peer deps for Windows
    frontend_dir = Path(__file__).parent / "frontend"
    if frontend_dir.exists():
        original_dir = os.getcwd()
        os.chdir(frontend_dir)
        
        # Try npm with legacy peer deps (Windows friendly)
        if not run_command("npm install --legacy-peer-deps", "Installing frontend dependencies (Windows mode)"):
            # Fallback: force install
            if not run_command("npm install --force", "Force installing frontend dependencies"):
                print("[WARNING] Frontend dependencies may have issues, but continuing...")
        
        os.chdir(original_dir)

    print("\n" + "=" * 60)
    print("[SUCCESS] SETUP COMPLETED!")
    print("=" * 60)
    print("Next steps:")
    print("  1. Run: python start_intelligence.py")
    print("  2. Wait for Chrome browser setup")
    print("  3. Open browser to: http://localhost:3000")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n[ERROR] Setup failed. Please check the errors above and try again.")
        sys.exit(1)
