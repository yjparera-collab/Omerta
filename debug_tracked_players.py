#!/usr/bin/env python3
"""
Debug script to check tracked players data
"""

import requests
import json

def test_tracked_players():
    """Test the tracked players endpoints"""
    
    print("🔍 DEBUGGING TRACKED PLAYERS SYSTEM")
    print("=" * 50)
    
    # Test scraping service direct
    try:
        print("1. Testing scraping service direct...")
        response = requests.get("http://localhost:5001/api/scraping/detective/targets")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Scraping service: {len(data.get('tracked_players', []))} tracked players")
            for player in data.get('tracked_players', []):
                print(f"      - {player.get('username')}: K:{player.get('kills')} S:{player.get('shots')}")
        else:
            print(f"   ❌ Scraping service error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Scraping service failed: {e}")
    
    # Test backend API
    try:
        print("\n2. Testing backend API...")
        response = requests.get("http://localhost:8001/api/intelligence/tracked-players")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Backend API: {len(data.get('tracked_players', []))} tracked players")
            for player in data.get('tracked_players', []):
                print(f"      - {player.get('username')}: K:{player.get('kills')} S:{player.get('shots')}")
        else:
            print(f"   ❌ Backend API error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Backend API failed: {e}")
    
    # Test database direct
    try:
        print("\n3. Testing database direct...")
        import sqlite3
        conn = sqlite3.connect('omerta_intelligence.db')
        
        # Check detective_targets table
        cursor = conn.execute('SELECT COUNT(*) FROM detective_targets WHERE is_active = 1')
        count = cursor.fetchone()[0]
        print(f"   📊 Detective targets in DB: {count}")
        
        if count > 0:
            cursor = conn.execute('SELECT username FROM detective_targets WHERE is_active = 1 LIMIT 10')
            for row in cursor.fetchall():
                print(f"      - {row[0]}")
        
        # Check player_cache table
        cursor = conn.execute('SELECT COUNT(*) FROM player_cache WHERE user_id IN (SELECT player_id FROM detective_targets WHERE is_active = 1)')
        cached_count = cursor.fetchone()[0]
        print(f"   💾 Cached data for tracked players: {cached_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Database check failed: {e}")
    
    print("\n" + "=" * 50)
    print("Debug complete!")

if __name__ == "__main__":
    test_tracked_players()