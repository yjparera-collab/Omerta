#!/usr/bin/env python3
"""
Create test data for username-first implementation testing
"""

import os
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

def create_test_data():
    """Create test data in MongoDB for username-first testing"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'omerta_intelligence')]
    
    print(f"Connected to MongoDB: {mongo_url}")
    print(f"Database: {db.name}")
    
    # Test players data with username as primary key
    test_players = [
        {
            "user_id": "2001",
            "username": "Kazuo",
            "data": json.dumps({
                "user_id": "2001",
                "username": "Kazuo",
                "kills": 15,
                "bullets_shot": {"total": 75},
                "wealth": 4,
                "plating": "High",
                "rank_name": "Soldier",
                "position": 3,
                "family_name": "TestFamily",
                "status": 1
            }),
            "last_updated": datetime.utcnow(),
            "priority": 1
        },
        {
            "user_id": "2002", 
            "username": "TestPlayer",
            "data": json.dumps({
                "user_id": "2002",
                "username": "TestPlayer",
                "kills": 8,
                "bullets_shot": {"total": 32},
                "wealth": 2,
                "plating": "Medium",
                "rank_name": "Associate",
                "position": 5,
                "family_name": "TestFamily2",
                "status": 1
            }),
            "last_updated": datetime.utcnow(),
            "priority": 1
        },
        {
            "user_id": "2003",
            "username": "AlphaPlayer", 
            "data": json.dumps({
                "user_id": "2003",
                "username": "AlphaPlayer",
                "kills": 22,
                "bullets_shot": {"total": 88},
                "wealth": 6,
                "plating": "Very High",
                "rank_name": "Capo",
                "position": 1,
                "family_name": "AlphaFamily",
                "status": 1
            }),
            "last_updated": datetime.utcnow(),
            "priority": 1
        },
        {
            "user_id": "2004",
            "username": "DeltaPlayer",
            "data": json.dumps({
                "user_id": "2004", 
                "username": "DeltaPlayer",
                "kills": 5,
                "bullets_shot": {"total": 20},
                "wealth": 1,
                "plating": "Low",
                "rank_name": "Picciotto",
                "position": 8,
                "family_name": "DeltaFamily",
                "status": 1
            }),
            "last_updated": datetime.utcnow(),
            "priority": 1
        }
    ]
    
    # Insert/update player cache data
    for player in test_players:
        db.player_cache.update_one(
            {"username": player["username"]},
            {"$set": player},
            upsert=True
        )
        print(f"✅ Added/Updated player cache for {player['username']}")
    
    # Add detective targets for username-first approach
    detective_targets = [
        {
            "username": "Kazuo",
            "player_id": "2001",
            "added_timestamp": datetime.utcnow(),
            "is_active": True
        },
        {
            "username": "TestPlayer", 
            "player_id": "2002",
            "added_timestamp": datetime.utcnow(),
            "is_active": True
        },
        {
            "username": "AlphaPlayer",
            "player_id": "2003", 
            "added_timestamp": datetime.utcnow(),
            "is_active": True
        }
    ]
    
    for target in detective_targets:
        db.detective_targets.update_one(
            {"username": target["username"]},
            {"$set": target},
            upsert=True
        )
        print(f"✅ Added detective target for {target['username']}")
    
    # Create some intelligence notifications
    notifications = [
        {
            "player_id": "2001",
            "username": "Kazuo",
            "notification_type": "kill_update",
            "message": "Kazuo has increased kills to 15",
            "data": json.dumps({"kills": 15, "previous_kills": 12}),
            "timestamp": datetime.utcnow(),
            "is_read": False
        },
        {
            "player_id": "2003",
            "username": "AlphaPlayer", 
            "notification_type": "plating_change",
            "message": "AlphaPlayer plating changed to Very High",
            "data": json.dumps({"plating": "Very High", "previous_plating": "High"}),
            "timestamp": datetime.utcnow(),
            "is_read": False
        }
    ]
    
    for notification in notifications:
        db.intelligence_notifications.insert_one(notification)
        print(f"✅ Added notification for {notification['username']}")
    
    # Verify data
    print(f"\n📊 Data Summary:")
    print(f"Player cache entries: {db.player_cache.count_documents({})}")
    print(f"Detective targets: {db.detective_targets.count_documents({'is_active': True})}")
    print(f"Intelligence notifications: {db.intelligence_notifications.count_documents({})}")
    
    # Test username-based queries
    print(f"\n🔍 Testing Username-Based Queries:")
    for username in ["Kazuo", "TestPlayer", "AlphaPlayer", "DeltaPlayer"]:
        player = db.player_cache.find_one({"username": username})
        if player:
            data = json.loads(player.get('data', '{}'))
            print(f"✅ {username}: kills={data.get('kills', 0)}, shots={data.get('bullets_shot', {}).get('total', 0)}")
        else:
            print(f"❌ {username}: not found")
    
    client.close()
    print(f"\n✅ Test data creation completed!")

if __name__ == "__main__":
    create_test_data()