#!/usr/bin/env python3
"""
Fix Windows-specific issues for Omerta Intelligence Dashboard
"""

import os
import json
from pathlib import Path

def fix_unicode_in_files():
    """Fix Unicode issues in Python files for Windows compatibility"""
    
    files_to_fix = [
        "scraping_service.py",
        "start_intelligence.py", 
        "install_dependencies.py",
        "backend/intelligence_server.py"
    ]
    
    # Unicode replacements for Windows
    replacements = {
        "🔧": "[SETUP]",
        "🎯": "[TARGET]", 
        "✅": "[OK]",
        "❌": "[ERROR]",
        "⚠️": "[WARNING]",
        "🚀": "[START]",
        "📡": "[COMM]",
        "🌐": "[WEB]",
        "🔌": "[CONNECT]",
        "📊": "[ANALYTICS]",
        "🕵️": "[DETECTIVE]",
        "🔒": "[SECURE]",
        "📋": "[COPY]",
        "📄": "[FILE]",
        "📁": "[DIR]",
        "🎉": "[SUCCESS]",
        "📦": "[PACKAGE]",
        "📏": "[SIZE]",
        "🛑": "[STOP]",
        "🔄": "[REFRESH]",
        "👥": "[PLAYERS]",
        "🚨": "[CRITICAL]",
        "🔫": "[SHOTS]",
        "👁️": "[INTEL]",
        "⚡": "[LIVE]",
        "🗄️": "[DB]",
        "📈": "[TRENDS]",
        "💾": "[CACHE]",
        "🕸️": "[SCRAPE]"
    }
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"Fixing Unicode in: {file_path}")
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace Unicode characters
            for unicode_char, replacement in replacements.items():
                content = content.replace(unicode_char, replacement)
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

def fix_frontend_package_json():
    """Fix frontend package.json dependency conflicts"""
    
    package_json_path = "frontend/package.json"
    if not os.path.exists(package_json_path):
        return
    
    print("Fixing frontend package.json...")
    
    # Updated package.json with compatible versions
    package_content = {
        "name": "omerta-intelligence-frontend",
        "version": "1.0.0",
        "private": True,
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
    
    with open(package_json_path, 'w', encoding='utf-8') as f:
        json.dump(package_content, f, indent=2)

def create_windows_install_script():
    """Create Windows-friendly install script"""
    
    install_content = '''#!/usr/bin/env python3
"""
Windows-compatible installer for Omerta Intelligence Dashboard
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

    print("\\n" + "=" * 60)
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
        print("\\n[ERROR] Setup failed. Please check the errors above and try again.")
        sys.exit(1)
'''
    
    with open("install_dependencies_windows.py", 'w', encoding='utf-8') as f:
        f.write(install_content)
    print("Created Windows-compatible installer: install_dependencies_windows.py")

def main():
    print("Fixing Windows compatibility issues...")
    
    fix_unicode_in_files()
    fix_frontend_package_json() 
    create_windows_install_script()
    
    print("\n" + "=" * 50)
    print("[SUCCESS] Windows fixes applied!")
    print("=" * 50)
    print("Now run: python install_dependencies_windows.py")

if __name__ == "__main__":
    main()