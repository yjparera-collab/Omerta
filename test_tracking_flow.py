#!/usr/bin/env python3
"""
Test the complete tracking flow step by step
"""

import requests
import json
import sqlite3
import os

def test_step_by_step():
    """Test each component in the tracking chain"""
    
    print("🔍 TESTING TRACKING FLOW STEP BY STEP")
    print("=" * 60)
    
    # Step 1: Test if database exists and has correct structure
    print("STEP 1: Database Structure Check")
    print("-" * 40)
    
    db_files = ['omerta_intelligence.db', 'omerta_hyper_intelligence.db']
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"✅ Found database: {db_file}")
            try:
                conn = sqlite3.connect(db_file)
                
                # Check tables
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                print(f"   📊 Tables: {', '.join(tables)}")
                
                # Check detective_targets if exists
                if 'detective_targets' in tables:
                    cursor = conn.execute('SELECT COUNT(*) FROM detective_targets WHERE is_active = 1')
                    count = cursor.fetchone()[0]
                    print(f"   🎯 Active detective targets: {count}")
                    
                    if count > 0:
                        cursor = conn.execute('SELECT username FROM detective_targets WHERE is_active = 1 LIMIT 5')
                        names = [row[0] for row in cursor.fetchall()]
                        print(f"   👤 Sample targets: {', '.join(names)}")
                
                conn.close()
            except Exception as e:
                print(f"   ❌ Database error: {e}")
        else:
            print(f"❌ Database not found: {db_file}")
    
    # Step 2: Test scraping service endpoints
    print(f"\nSTEP 2: Scraping Service Test")
    print("-" * 40)
    
    try:
        # Test basic status
        response = requests.get("http://localhost:5001/api/scraping/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Scraping service: ONLINE")
            print(f"   📊 Cached players: {data.get('cached_players', 0)}")
            print(f"   🎯 Detective targets: {data.get('detective_targets', 0)}")
        else:
            print(f"❌ Scraping service status: {response.status_code}")
    except Exception as e:
        print(f"❌ Scraping service: OFFLINE ({e})")
    
    try:
        # Test detective targets endpoint
        response = requests.get("http://localhost:5001/api/scraping/detective/targets", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tracked = data.get('tracked_players', [])
            print(f"✅ Detective targets endpoint: {len(tracked)} players")
            for player in tracked[:3]:
                print(f"   👤 {player.get('username')}: K:{player.get('kills')} S:{player.get('shots')}")
        else:
            print(f"❌ Detective targets endpoint: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Detective targets endpoint: {e}")
    
    # Step 3: Test backend API
    print(f"\nSTEP 3: Backend API Test")
    print("-" * 40)
    
    try:
        # Test status
        response = requests.get("http://localhost:8001/api/status", timeout=5)
        if response.status_code == 200:
            print(f"✅ Backend API: ONLINE")
        else:
            print(f"❌ Backend API status: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend API: OFFLINE ({e})")
    
    try:
        # Test tracked players endpoint
        response = requests.get("http://localhost:8001/api/intelligence/tracked-players", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tracked = data.get('tracked_players', [])
            print(f"✅ Backend tracked players: {len(tracked)} players")
            for player in tracked[:3]:
                print(f"   👤 {player.get('username')}: K:{player.get('kills')} S:{player.get('shots')}")
        else:
            print(f"❌ Backend tracked players: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Backend tracked players: {e}")
    
    # Step 4: Test adding a detective target
    print(f"\nSTEP 4: Test Adding Detective Target")
    print("-" * 40)
    
    try:
        # Try to add a test player
        test_data = {"usernames": ["TestPlayer123"]}
        response = requests.post("http://localhost:8001/api/intelligence/detective/add", 
                               json=test_data, timeout=5)
        if response.status_code == 200:
            print(f"✅ Successfully added test detective target")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Failed to add detective target: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Add detective target: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSIS COMPLETE")

if __name__ == "__main__":
    test_step_by_step()