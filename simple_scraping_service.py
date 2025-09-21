#!/usr/bin/env python3
import os
import json
from datetime import datetime
from flask import Flask, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# MongoDB Setup
def init_mongodb():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'omerta_intelligence')]
    print(f"[DB] Connected to MongoDB: {mongo_url}")
    return db

# Flask App
app = Flask(__name__)
db = init_mongodb()

@app.route('/api/scraping/status')
def get_status():
    """Get scraping service status"""
    try:
        player_count = db.player_cache.count_documents({})
        target_count = db.detective_targets.count_documents({"is_active": True})
        
        return jsonify({
            "status": "online",
            "cached_players": player_count,
            "detective_targets": target_count,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/players')
def get_players():
    """Get all players from cache"""
    try:
        players = list(db.player_cache.find({}, {"_id": 0}))
        
        # Convert MongoDB data to expected format
        formatted_players = []
        for player in players:
            formatted_players.append({
                "id": player.get("user_id"),
                "uname": player.get("username"),
                "f_name": player.get("family_name"),
                "rank_name": player.get("rank_name"),
                "position": player.get("position", 0),
                "status": player.get("status", 1)
            })
        
        return jsonify({
            "players": formatted_players,
            "count": len(formatted_players),
            "last_updated": datetime.utcnow().isoformat()
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
                player_info.update({
                    "kills": cached_data.get('kills', 0),
                    "shots": cached_data.get('bullets_shot', 0),
                    "wealth": cached_data.get('wealth', 'Unknown'),
                    "plating": cached_data.get('plating', 'Unknown'),
                    "last_updated": cached_data.get('last_updated')
                })
            
            result.append(player_info)
        
        return jsonify({
            "tracked_players": result,
            "count": len(result),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/notifications')
def get_notifications():
    """Get intelligence notifications"""
    try:
        notifications = list(db.intelligence_notifications.find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).limit(50))
        
        # Format notifications for frontend
        formatted_notifications = []
        for notif in notifications:
            formatted_notifications.append({
                "type": notif.get("notification_type"),
                "username": notif.get("username"),
                "message": notif.get("message"),
                "timestamp": notif.get("timestamp").isoformat() if notif.get("timestamp") else None,
                "is_read": notif.get("is_read", False)
            })
        
        return jsonify({
            "notifications": formatted_notifications,
            "count": len(formatted_notifications),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/player/<player_id>')
def get_player_details(player_id):
    """Get detailed player information"""
    try:
        player = db.player_cache.find_one({"user_id": player_id}, {"_id": 0})
        if not player:
            return jsonify({"error": "Player not found"}), 404
        
        # Return detailed player data
        return jsonify({
            "id": player.get("user_id"),
            "username": player.get("username"),
            "family_name": player.get("family_name"),
            "rank_name": player.get("rank_name"),
            "position": player.get("position", 0),
            "status": player.get("status", 1),
            "kills": player.get("kills", 0),
            "bullets_shot": {"total": player.get("bullets_shot", 0)},
            "wealth": player.get("wealth", 0),
            "plating": player.get("plating", "Unknown"),
            "last_updated": player.get("last_updated")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("[START] Simple Scraping Service starting on port 5001...")
    app.run(debug=False, host='127.0.0.1', port=5001)