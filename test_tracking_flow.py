#!/usr/bin/env python3
"""
Test the complete tracking flow step by step
"""

import requests
import json
import os
from pymongo import MongoClient

def test_step_by_step():
    """Test each component in the tracking chain"""
    
    print("🔍 TESTING TRACKING FLOW STEP BY STEP")
    print("=" * 60)
    
    # Step 1: Test MongoDB connection and collections
    print("STEP 1: MongoDB Connection Check")
    print("-" * 40)
    
    try:
        client = MongoClient('mongodb://localhost:27017')
        db = client['omerta_intelligence']
        
        print("✅ MongoDB connection: SUCCESS")
        
        # Check collections
        collections = db.list_collection_names()
        print(f"   📊 Collections: {', '.join(collections) if collections else 'None'}")
        
        # Check detective_targets collection
        if 'detective_targets' in collections:
            targets_count = db.detective_targets.count_documents({"is_active": True})
            print(f"   🎯 Active detective targets: {targets_count}")
            
            if targets_count > 0:
                sample_targets = list(db.detective_targets.find({"is_active": True}, {"username": 1}).limit(5))
                names = [target.get('username', 'Unknown') for target in sample_targets]
                print(f"   👤 Sample targets: {', '.join(names)}")
        else:
            print(f"   ⚠️  No detective_targets collection found")
            
        # Check tracked_players collection  
        if 'tracked_players' in collections:
            tracked_count = db.tracked_players.count_documents({})
            print(f"   👥 Tracked players: {tracked_count}")
        else:
            print(f"   ⚠️  No tracked_players collection found")
            
        client.close()
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
    
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