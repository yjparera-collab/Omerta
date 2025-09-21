#!/usr/bin/env python3
"""
Test Scraping Service - Username-First Implementation
Simple Flask service for testing without Chrome dependency
"""

import time
from datetime import datetime
import json
import threading
from flask import Flask, request, jsonify
import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- MongoDB SETUP ---
def init_mongodb():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'omerta_intelligence')]
    
    print(f"[DB] Connected to MongoDB: {mongo_url}")
    print(f"[DB] Database: {db.name}")
    
    return db

# --- SIMPLE DATA MANAGER ---
class TestIntelligenceDataManager:
    def __init__(self):
        self.db = init_mongodb()
        self.detective_targets = set()
        self.load_detective_targets()

    def load_detective_targets(self):
        """Load active detective targets from MongoDB"""
        try:
            targets = list(self.db.detective_targets.find({"is_active": True}))
            self.detective_targets = {target['username'] for target in targets}
            print(f"[DB] Loaded {len(self.detective_targets)} detective targets")
        except Exception as e:
            print(f"[ERROR] Loading detective targets: {e}")

    def add_detective_targets(self, usernames):
        """Add new detective targets to MongoDB"""
        added_count = 0
        for username in usernames:
            try:
                result = self.db.detective_targets.update_one(
                    {"username": username},
                    {
                        "$set": {
                            "username": username,
                            "player_id": f"player_{username.lower()}",
                            "added_timestamp": datetime.utcnow(),
                            "is_active": True
                        }
                    },
                    upsert=True
                )
                if result.upserted_id or result.modified_count > 0:
                    self.detective_targets.add(username)
                    added_count += 1
                    print(f"[TARGET] Added detective target: {username}")
            except Exception as e:
                print(f"[ERROR] Adding detective target {username}: {e}")
        
        return {"added": added_count, "total": len(self.detective_targets)}

    def get_detective_targets(self):
        """Get all active detective targets with their latest data - USERNAME FIRST"""
        try:
            targets = list(self.db.detective_targets.find({"is_active": True}))
            result = []
            
            for target in targets:
                username = target['username']
                # Get latest cached data for this target BY USERNAME
                cached_data = self.db.player_cache.find_one({"username": username})
                
                player_info = {
                    "username": username,
                    "player_id": target.get('player_id', ''),  # Keep for legacy, but UI should ignore
                    "added_timestamp": target.get('added_timestamp', ''),
                    "last_updated": None
                }
                
                if cached_data:
                    try:
                        raw = json.loads(cached_data.get('data', '{}'))
                        # Handle the data wrapper - unwrap if present
                        inner = raw.get('data', raw) if isinstance(raw, dict) else raw
                        
                        # Normalize bullets_shot total
                        bs = inner.get('bullets_shot') if isinstance(inner, dict) else None
                        shots_total = None
                        if isinstance(bs, dict):
                            shots_total = bs.get('total')
                        else:
                            shots_total = bs
                            
                        # Only add data if we have actual values, not fake defaults
                        if inner.get('kills') is not None:
                            player_info["kills"] = inner.get('kills')
                        if shots_total is not None:
                            player_info["shots"] = shots_total
                        if inner.get('wealth') is not None:
                            player_info["wealth"] = inner.get('wealth')
                        if inner.get('plating') is not None:
                            player_info["plating"] = inner.get('plating')
                            
                        player_info["last_updated"] = cached_data.get('last_updated')
                        
                    except Exception as e:
                        print(f"[TARGETS] Parse error for {username}: {e}")
                
                result.append(player_info)
            
            return result
        except Exception as e:
            print(f"[ERROR] Getting detective targets: {e}")
            return []

    def get_cached_players_count(self):
        """Get count of cached players"""
        try:
            return self.db.player_cache.count_documents({})
        except:
            return 0

    def cache_player_data(self, user_id, username, data):
        """Cache player data in MongoDB - USERNAME FIRST approach"""
        try:
            # Prioritize username - it's the primary key now
            username_str = str(username) if username else None
            user_id_str = str(user_id) if user_id else None
            
            if not username_str:
                if user_id_str:
                    username_str = f"Player_{user_id_str}"
                else:
                    raise ValueError("No valid username or user_id provided")
            
            # Create document with username as primary key
            doc = {
                "username": username_str,  # PRIMARY KEY
                "user_id": user_id_str,    # Secondary for legacy compatibility
                "data": json.dumps(data, default=str),
                "last_updated": datetime.utcnow(),
                "priority": 1
            }
            
            # Use username as the unique identifier
            result = self.db.player_cache.update_one(
                {"username": username_str},
                {"$set": doc},
                upsert=True
            )
            
            # Verify the operation
            if result.upserted_id or result.modified_count > 0:
                print(f"[CACHE] ✅ Cached data for {username_str} (ID: {user_id_str})")
                return True
            else:
                print(f"[CACHE] ⚠️ No changes made for {username_str}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Caching player data for {username} (ID: {user_id}): {e}")
            return False

# --- Flask App Setup ---
app = Flask(__name__)
data_manager = TestIntelligenceDataManager()

@app.route('/api/scraping/status')
def get_status():
    """Get scraping service status"""
    try:
        return jsonify({
            "status": "online",
            "mode": "test_mode",
            "cached_players": data_manager.get_cached_players_count(),
            "detective_targets": len(data_manager.detective_targets),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/detective/targets')
def get_detective_targets():
    """Get all detective targets with their data"""
    try:
        targets = data_manager.get_detective_targets()
        return jsonify({
            "tracked_players": targets,
            "count": len(targets),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/detective/add', methods=['POST'])
def add_detective_targets():
    """Add new detective targets"""
    try:
        data = request.get_json()
        usernames = data.get('usernames', [])
        
        if not usernames:
            return jsonify({"error": "No usernames provided"}), 400
            
        result = data_manager.add_detective_targets(usernames)
        return jsonify({
            "message": f"Added {result['added']} detective targets",
            "added": result['added'],
            "total_targets": result['total'],
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/player-username/<username>')
def get_player_detail_by_username(username):
    """Get specific player details by USERNAME (primary method)"""
    try:
        # Find player in cache by username
        player = data_manager.db.player_cache.find_one(
            {"username": username}, 
            {"_id": 0}
        )
        
        if not player:
            return jsonify({"error": f"Player {username} not found"}), 404
        
        # Parse player data and handle wrapper
        try:
            raw_data = json.loads(player.get('data', '{}'))
            # Handle the data wrapper if present
            if isinstance(raw_data, dict) and 'data' in raw_data:
                player_data = raw_data['data']
            else:
                player_data = raw_data
            return jsonify(player_data)
        except Exception as e:
            print(f"[API] Parse error for {username}: {e}")
            return jsonify({"error": "Invalid player data"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/players')
def get_players():
    """Get all cached players"""
    try:
        # Get sample cached players from MongoDB
        players = list(
            data_manager.db.player_cache
            .find({}, {"_id": 0})
            .sort("last_updated", -1)
            .limit(100)
        )
        
        # Parse player data
        parsed_players = []
        for player in players:
            try:
                player_data = json.loads(player.get('data', '{}'))
                parsed_players.append(player_data)
            except:
                pass
        
        return jsonify({
            "players": parsed_players,
            "count": len(parsed_players),
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "test_mode"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Create some test data on startup
def create_test_data():
    """Create test data for username-first testing"""
    print("[TEST] Creating test data...")
    
    test_players = [
        {
            "username": "Kazuo",
            "user_id": "2001", 
            "data": {
                "id": "2001",
                "uname": "Kazuo", 
                "rank_name": "Soldier",
                "position": 3,
                "kills": 15,
                "bullets_shot": {"total": 75},
                "wealth": 4,
                "plating": "High",
                "status": 1,
                "f_name": "TestFamily"
            }
        },
        {
            "username": "TestPlayer", 
            "user_id": "2002",
            "data": {
                "id": "2002",
                "uname": "TestPlayer",
                "rank_name": "Mobster", 
                "position": 5,
                "kills": 8,
                "bullets_shot": {"total": 42},
                "wealth": 2,
                "plating": "Medium",
                "status": 1,
                "f_name": "AlphaFamily"
            }
        },
        {
            "username": "AlphaPlayer",
            "user_id": "2003", 
            "data": {
                "id": "2003",
                "uname": "AlphaPlayer",
                "rank_name": "Chief",
                "position": 1,
                "kills": 23,
                "bullets_shot": {"total": 95},
                "wealth": 5,
                "plating": "Very High",
                "status": 1,
                "f_name": "BetaFamily"
            }
        }
    ]
    
    for player in test_players:
        data_manager.cache_player_data(
            player["user_id"],
            player["username"], 
            player["data"]
        )
    
    print(f"[TEST] Created {len(test_players)} test players")

if __name__ == '__main__':
    try:
        print("\n[SETUP] Starting Test MongoDB-based Omerta Intelligence Scraping Service...")
        print("🧪 TEST MODE: No browser dependency - using cached data only")
        
        # Create test data
        create_test_data()
        
        print(f"\n" + "="*60)
        print(f"🧪 TEST MONGODB OMERTA INTELLIGENCE SCRAPING ACTIVE")
        print(f"[CACHE] Using MongoDB for persistent data - USERNAME FIRST")
        print(f"[TARGET] Ready for FastAPI integration on port 8001") 
        print(f"[API] Flask test API running on http://127.0.0.1:5001")
        print(f"="*60)

        app.run(debug=False, use_reloader=False, port=5001, host='127.0.0.1')

    except KeyboardInterrupt:
        print("\n\n👋 Test scraping service stopped by user.")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")