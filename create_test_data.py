#!/usr/bin/env python3
import os
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

def create_test_data():
    """Create test player data for testing sorting functionality"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'omerta_intelligence')]
    
    print(f"Connected to MongoDB: {mongo_url}")
    print(f"Database: {db.name}")
    
    # Clear existing data
    db.player_cache.delete_many({})
    print("Cleared existing player cache")
    
    # Create test players with various positions for sorting test
    test_players = [
        {
            "user_id": "1001",
            "username": "AlphaPlayer",
            "family_name": "TestFamily1",
            "rank_name": "Godfather",
            "position": 1,
            "status": 1,
            "kills": 15,
            "bullets_shot": {"total": 50},
            "wealth": 5,
            "plating": "High",
            "last_updated": datetime.utcnow()
        },
        {
            "user_id": "1002", 
            "username": "BetaPlayer",
            "family_name": "TestFamily2",
            "rank_name": "Chief",
            "position": 2,
            "status": 1,
            "kills": 12,
            "bullets_shot": {"total": 40},
            "wealth": 4,
            "plating": "Medium",
            "last_updated": datetime.utcnow()
        },
        {
            "user_id": "1003",
            "username": "GammaPlayer", 
            "family_name": "TestFamily1",
            "rank_name": "Soldier",
            "position": 3,
            "status": 1,
            "kills": 8,
            "bullets_shot": {"total": 30},
            "wealth": 3,
            "plating": "Low",
            "last_updated": datetime.utcnow()
        },
        {
            "user_id": "1004",
            "username": "DeltaPlayer",
            "family_name": "TestFamily3", 
            "rank_name": "Associate",
            "position": 0,  # Unranked
            "status": 1,
            "kills": 5,
            "bullets_shot": {"total": 20},
            "wealth": 2,
            "plating": "None",
            "last_updated": datetime.utcnow()
        },
        {
            "user_id": "1005",
            "username": "EpsilonPlayer",
            "family_name": "TestFamily2",
            "rank_name": "Mobster", 
            "position": 0,  # Unranked
            "status": 1,
            "kills": 3,
            "bullets_shot": {"total": 15},
            "wealth": 1,
            "plating": "None",
            "last_updated": datetime.utcnow()
        },
        {
            "user_id": "1006",
            "username": "ZetaPlayer",
            "family_name": "TestFamily1",
            "rank_name": "Bruglione",
            "position": 4,
            "status": 1,
            "kills": 20,
            "bullets_shot": {"total": 60},
            "wealth": 4,
            "plating": "High",
            "last_updated": datetime.utcnow()
        },
        {
            "user_id": "1007",
            "username": "EtaPlayer",
            "family_name": "TestFamily3",
            "rank_name": "Capodecina",
            "position": 5,
            "status": 1,
            "kills": 18,
            "bullets_shot": {"total": 55},
            "wealth": 5,
            "plating": "Very High",
            "last_updated": datetime.utcnow()
        },
        {
            "user_id": "1008",
            "username": "ThetaPlayer",
            "family_name": "TestFamily2",
            "rank_name": "Thief",
            "position": 0,  # Unranked
            "status": 1,
            "kills": 1,
            "bullets_shot": {"total": 5},
            "wealth": 0,
            "plating": "None",
            "last_updated": datetime.utcnow()
        },
        {
            "user_id": "1009",
            "username": "IotaPlayer",
            "family_name": "TestFamily1",
            "rank_name": "Local Chief",
            "position": 6,
            "status": 1,
            "kills": 10,
            "bullets_shot": {"total": 35},
            "wealth": 3,
            "plating": "Medium",
            "last_updated": datetime.utcnow()
        },
        {
            "user_id": "1010",
            "username": "KappaPlayer",
            "family_name": "TestFamily3",
            "rank_name": "Assassin",
            "position": 0,  # Unranked
            "status": 1,
            "kills": 7,
            "bullets_shot": {"total": 25},
            "wealth": 2,
            "plating": "Low",
            "last_updated": datetime.utcnow()
        }
    ]
    
    # Insert test players
    for player in test_players:
        # Store as expected by the scraping service
        player_data = {
            "user_id": player["user_id"],
            "username": player["username"],
            "family_name": player["family_name"],
            "rank_name": player["rank_name"],
            "position": player["position"],
            "status": player["status"],
            "kills": player["kills"],
            "bullets_shot": player["bullets_shot"]["total"],
            "wealth": player["wealth"],
            "plating": player["plating"],
            "data": json.dumps(player),
            "last_updated": player["last_updated"],
            "priority": 1
        }
        
        db.player_cache.update_one(
            {"user_id": player["user_id"]},
            {"$set": player_data},
            upsert=True
        )
    
    print(f"Created {len(test_players)} test players")
    
    # Also create some detective targets for testing
    db.detective_targets.delete_many({})
    detective_targets = [
        {
            "username": "AlphaPlayer",
            "player_id": "1001",
            "added_timestamp": datetime.utcnow(),
            "is_active": True
        },
        {
            "username": "DeltaPlayer", 
            "player_id": "1004",
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
    
    print(f"Created {len(detective_targets)} detective targets")
    
    # Verify data
    player_count = db.player_cache.count_documents({})
    target_count = db.detective_targets.count_documents({"is_active": True})
    
    print(f"Verification: {player_count} players, {target_count} active targets in database")
    
    client.close()
    print("Test data creation completed!")

if __name__ == "__main__":
    create_test_data()