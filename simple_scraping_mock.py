#!/usr/bin/env python3
"""
Simple mock scraping service for testing username-first implementation
"""

from flask import Flask, jsonify
import os
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

app = Flask(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'omerta_intelligence')]

@app.route('/api/scraping/status')
def get_status():
    """Get scraping service status"""
    try:
        return jsonify({
            "status": "online",
            "cached_players": db.player_cache.count_documents({}),
            "detective_targets": db.detective_targets.count_documents({"is_active": True}),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/players')
def get_players():
    """Get all players from cache"""
    try:
        players = list(db.player_cache.find({}, {"_id": 0}))
        formatted_players = []
        for player in players:
            try:
                data = json.loads(player.get('data', '{}'))
                formatted_players.append({
                    "id": player.get("user_id"),
                    "uname": player.get("username"),
                    "f_name": data.get("family_name", ""),
                    "rank_name": data.get("rank_name", "Unknown"),
                    "position": data.get("position", 0),
                    "status": data.get("status", 1)
                })
            except:
                pass
        
        return jsonify({
            "players": formatted_players,
            "count": len(formatted_players),
            "last_updated": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/player-username/<username>')
def get_player_detail_by_username(username):
    """Get specific player details by USERNAME (primary method)"""
    try:
        # Find player in cache by username
        player = db.player_cache.find_one(
            {"username": username}, 
            {"_id": 0}
        )
        
        if not player:
            return jsonify({"error": f"Player {username} not found"}), 404
        
        # Parse player data
        try:
            player_data = json.loads(player.get('data', '{}'))
        except:
            player_data = {}
        
        # Return detailed player data with username as primary key
        return jsonify({
            "username": username,
            "user_id": player_data.get("user_id", player.get("user_id")),
            "kills": player_data.get("kills", 0),
            "bullets_shot": player_data.get("bullets_shot", {"total": 0}),
            "wealth": player_data.get("wealth", 0),
            "plating": player_data.get("plating", "Unknown"),
            "rank_name": player_data.get("rank_name", "Unknown"),
            "position": player_data.get("position", 0),
            "family_name": player_data.get("family_name", ""),
            "status": player_data.get("status", 1),
            "last_updated": player.get("last_updated")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/detective/targets')
def get_detective_targets():
    """Get all detective targets with their data"""
    try:
        targets = list(db.detective_targets.find({"is_active": True}))
        result = []
        
        for target in targets:
            # Get latest cached data for this target
            cached_data = db.player_cache.find_one({"username": target['username']})
            
            player_info = {
                "username": target['username'],
                "player_id": target.get('player_id', ''),
                "added_timestamp": target.get('added_timestamp', ''),
                "kills": 0,
                "shots": 0,
                "wealth": "Unknown",
                "plating": "Unknown",
                "last_updated": None
            }
            
            if cached_data:
                try:
                    data = json.loads(cached_data.get('data', '{}'))
                    player_info.update({
                        "kills": data.get('kills', 0),
                        "shots": data.get('bullets_shot', {}).get('total', 0) if isinstance(data.get('bullets_shot'), dict) else data.get('bullets_shot', 0),
                        "wealth": data.get('wealth', 'Unknown'),
                        "plating": data.get('plating', 'Unknown'),
                        "last_updated": cached_data.get('last_updated')
                    })
                except:
                    pass
            
            result.append(player_info)
        
        return jsonify({
            "tracked_players": result,
            "count": len(result),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/detective/add', methods=['POST'])
def add_detective_targets():
    """Add new detective targets"""
    from flask import request
    try:
        data = request.get_json()
        usernames = data.get('usernames', [])
        
        if not usernames:
            return jsonify({"error": "No usernames provided"}), 400
            
        added_count = 0
        for username in usernames:
            try:
                result = db.detective_targets.update_one(
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
                    added_count += 1
            except Exception as e:
                print(f"Error adding detective target {username}: {e}")
        
        return jsonify({
            "message": f"Added {added_count} detective targets",
            "added": added_count,
            "total_targets": db.detective_targets.count_documents({"is_active": True}),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Simple Mock Scraping Service on port 5001...")
    app.run(debug=False, host='127.0.0.1', port=5001)