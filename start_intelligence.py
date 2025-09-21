#!/usr/bin/env python3
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
    print(f"[START] Starting {service_name} on port {port}...")
    try:
        process = subprocess.Popen([
            sys.executable, script_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(3)  # Give it time to start
        
        if process.poll() is None:
            print(f"[OK] {service_name} started successfully (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"[ERROR] {service_name} failed to start:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return None
    except Exception as e:
        print(f"[ERROR] Error starting {service_name}: {e}")
        return None

def main():
    print("=" * 60)
    print("[TARGET] OMERTA WAR INTELLIGENCE DASHBOARD")
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
        print(f"[ERROR] Scraping service script not found: {scraping_script}")
        return

    if not api_script.exists():
        print(f"[ERROR] API server script not found: {api_script}")
        return

    processes = []

    try:
        # Start Flask scraping service
        scraping_process = start_service(str(scraping_script), "Flask Scraping Service", 5001)
        if scraping_process:
            processes.append(("Scraping Service", scraping_process))
        else:
            print("[ERROR] Failed to start scraping service. Exiting.")
            return

        # Wait a bit for scraping service to fully initialize
        time.sleep(5)

        # Start FastAPI dashboard
        api_process = start_service(str(api_script), "FastAPI Dashboard API", 8001)
        if api_process:
            processes.append(("Dashboard API", api_process))
        else:
            print("[ERROR] Failed to start dashboard API. Stopping scraping service.")
            scraping_process.terminate()
            return

        print("\n" + "=" * 60)
        print("[TARGET] OMERTA INTELLIGENCE DASHBOARD ACTIVE!")
        print("=" * 60)
        print("[COMM] Services Status:")
        for name, process in processes:
            status = "RUNNING" if process.poll() is None else "STOPPED"
            print(f"  {name}: {status} (PID: {process.pid})")
        
        print("\n[WEB] Access Points:")
        print("  • React Frontend: http://localhost:3000")
        print("  • API Dashboard: http://localhost:8001")
        print("  • Scraping Service: http://localhost:5001")
        print("  • WebSocket: ws://localhost:8001/ws")
        
        print("\n[COPY] Instructions:")
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
                    print(f"[WARNING]  {name} has stopped unexpectedly!")
                    # Could implement restart logic here

    except KeyboardInterrupt:
        print("\n[STOP] Shutting down services...")
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