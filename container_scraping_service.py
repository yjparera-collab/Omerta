#!/usr/bin/env python3
"""
Container Scraping Service - Fallback for development
This service provides cached data and explains the Cloudflare issue
For real scraping, use mongodb_scraping_service_windows.py on Windows
"""

import time
from datetime import datetime
import json
import threading
from flask import Flask, request, jsonify
import os
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
class ContainerIntelligenceManager:
    def __init__(self):
        self.db = init_mongodb()
        self.detective_targets = set()
        self.load_detective_targets()
        self.ensure_sample_data()
        
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

    def ensure_sample_data(self):
        """Ensure we have sample data with REAL values for demonstration"""
        sample_players = [
            {
                "username": "AlphaPlayer",
                "user_id": "2003", 
                "data": {
                    "id": "2003",
                    "uname": "AlphaPlayer",
                    "username": "AlphaPlayer", 
                    "rank_name": "Chief",
                    "position": 1,
                    "kills": 23,
                    "bullets_shot": {"total": 95},
                    "wealth": 5,
                    "plating": "Very High",
                    "status": 1,
                    "f_name": "BetaFamily"
                }
            },
            {
                "username": "DeltaPlayer",
                "user_id": "1004",
                "data": {
                    "id": "1004", 
                    "uname": "DeltaPlayer",
                    "username": "DeltaPlayer",
                    "rank_name": "Soldier",
                    "position": 8,
                    "kills": 5,
                    "bullets_shot": {"total": 20},
                    "wealth": 1,
                    "plating": "Low",
                    "status": 1,
                    "f_name": "DeltaFamily"
                }
            },
            {
                "username": "Kazuo",
                "user_id": "2001", 
                "data": {
                    "id": "2001",
                    "uname": "Kazuo",
                    "username": "Kazuo",
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
                    "username": "TestPlayer",
                    "rank_name": "Mobster",
                    "position": 5,
                    "kills": 8,
                    "bullets_shot": {"total": 42},
                    "wealth": 2,
                    "plating": "Medium",
                    "status": 1,
                    "f_name": "AlphaFamily"
                }
            }
        ]
        
        for player in sample_players:
            try:
                doc = {
                    "username": player["username"],
                    "user_id": player["user_id"],
                    "data": json.dumps(player["data"], default=str),
                    "last_updated": datetime.utcnow(),
                    "priority": 1
                }
                
                self.db.player_cache.update_one(
                    {"username": player["username"]},
                    {"$set": doc},
                    upsert=True
                )
            except Exception as e:
                print(f"[SAMPLE] Error creating sample data for {player['username']}: {e}")

    def get_detective_targets(self):
        """Get all detective targets with cached data"""
        try:
            targets = list(self.db.detective_targets.find({"is_active": True}))
            result = []
            
            for target in targets:
                username = target['username']
                cached_data = self.db.player_cache.find_one({"username": username})
                
                player_info = {
                    "username": username,
                    "player_id": target.get('player_id', ''),
                    "added_timestamp": target.get('added_timestamp', ''),
                    "last_updated": None
                }
                
                if cached_data:
                    try:
                        raw = json.loads(cached_data.get('data', '{}'))
                        inner = raw.get('data', raw) if isinstance(raw, dict) and 'data' in raw else raw
                        
                        if isinstance(inner, dict):
                            if inner.get('kills') is not None:
                                player_info["kills"] = inner.get('kills')
                            
                            bullets_shot = inner.get('bullets_shot')
                            if bullets_shot is not None:
                                if isinstance(bullets_shot, dict):
                                    shots = bullets_shot.get('total')
                                else:
                                    shots = bullets_shot
                                if shots is not None:
                                    player_info["shots"] = shots
                            
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

# --- FLASK APP ---
app = Flask(__name__)
data_manager = ContainerIntelligenceManager()

@app.route('/api/scraping/status')
def get_status():
    """Get scraping service status"""
    try:
        return jsonify({
            "status": "online",
            "mode": "container_demo_mode",
            "cached_players": data_manager.get_cached_players_count(),
            "detective_targets": len(data_manager.detective_targets),
            "warning": "This is demo mode. For real Barafranca scraping, run mongodb_scraping_service_windows.py on Windows",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/debug-info')
def get_debug_info():
    """Debug info about Cloudflare issue"""
    try:
        return jsonify({
            "cloudflare_problem": {
                "issue": "Barafranca.com uses Cloudflare protection that blocks automated requests",
                "evidence": "Direct curl/requests get HTTP 403 Forbidden responses",
                "solution": "Must use visible Chrome browser with manual interaction on Windows",
                "why_container_fails": "Container has no display, Chrome crashes, can't solve CAPTCHAs"
            },
            "api_tests": {
                "list_api": "https://barafranca.com/index.php?module=API&action=users",
                "detail_api": "https://barafranca.com/index.php?module=API&action=user&name=teg",
                "expected_result": "403 Forbidden due to Cloudflare",
                "curl_test": "curl 'https://barafranca.com/index.php?module=API&action=user&name=teg'"
            },
            "working_setup": {
                "environment": "Windows with visible Chrome browser",
                "service": "mongodb_scraping_service_windows.py",
                "requirements": "undetected-chromedriver + manual CAPTCHA solving"
            },
            "current_data": {
                "cached_players": data_manager.get_cached_players_count(),
                "detective_targets": len(data_manager.detective_targets),
                "data_source": "Sample data for UI testing"
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/detective/targets')
def get_detective_targets():
    """Get all detective targets with data"""
    try:
        targets = data_manager.get_detective_targets()
        return jsonify({
            "tracked_players": targets,
            "count": len(targets),
            "note": "Using cached sample data - real scraping requires Windows setup",
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
            "message": f"Added {result['added']} detective targets (demo mode)",
            "added": result['added'],
            "total_targets": result['total'],
            "note": "Real data updates require Windows scraping service",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/player-username/<username>')
def get_player_by_username(username):
    """Get player details by username"""
    try:
        player = data_manager.db.player_cache.find_one({"username": username}, {"_id": 0})
        
        if not player:
            return jsonify({"error": f"Player {username} not found in cache"}), 404
        
        try:
            raw_data = json.loads(player.get('data', '{}'))
            if isinstance(raw_data, dict) and 'data' in raw_data:
                player_data = raw_data['data']
            else:
                player_data = raw_data
            return jsonify(player_data)
        except Exception as e:
            return jsonify({"error": "Invalid player data"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/players')
def get_players():
    """Get all cached players"""
    try:
        players = list(
            data_manager.db.player_cache
            .find({}, {"_id": 0})
            .sort("last_updated", -1)
            .limit(50)
        )
        
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
            "note": "Sample data for demo - real data requires Windows scraping service",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    try:
        print("\n" + "="*70)
        print("🎯 OMERTA INTELLIGENCE SCRAPING SERVICE - CONTAINER DEMO MODE")
        print("⚠️  CLOUDFLARE PROTECTION ACTIVE - REAL SCRAPING REQUIRES WINDOWS")
        print("🔧 USERNAME-FIRST ARCHITECTURE WITH SAMPLE DATA")
        print("="*70)
        
        print(f"\n🚨 IMPORTANT CLOUDFLARE ISSUE:")
        print(f"   • Barafranca.com blocks automated requests (HTTP 403)")
        print(f"   • Container can't run visible Chrome browser")
        print(f"   • For real scraping: use mongodb_scraping_service_windows.py on Windows")
        print(f"   • This service provides sample data for UI testing")
        
        print(f"\n✅ Demo Services Starting:")
        print(f"📊 API Status: http://127.0.0.1:5001/api/scraping/status")
        print(f"🐛 Debug Info: http://127.0.0.1:5001/api/scraping/debug-info")
        print(f"💾 Sample Players: {data_manager.get_cached_players_count()}")
        print(f"🎯 Detective Targets: {len(data_manager.detective_targets)}")
        
        app.run(debug=False, use_reloader=False, port=5001, host='127.0.0.1')

    except KeyboardInterrupt:
        print("\n👋 Container scraping service stopped.")
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")