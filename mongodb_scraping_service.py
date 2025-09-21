import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import threading
from flask import Flask, request, jsonify
from queue import Queue, PriorityQueue
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# --- CONFIGURATIE ---
USER_LIST_URL = "https://barafranca.com/index.php?module=API&action=users"
USER_DETAIL_URL_TEMPLATE = "https://barafranca.com/index.php?module=API&action=user&name={}"
MAIN_LIST_INTERVAL = 30
MAX_CONCURRENT_TABS = 2
CACHE_DURATION = 30  # 30 seconden cache voor detective targets
BATCH_SIZE = 5

# --- MongoDB SETUP ---
def init_mongodb():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'omerta_intelligence')]
    
    print(f"[DB] Connected to MongoDB: {mongo_url}")
    print(f"[DB] Database: {db.name}")
    
    # Create indexes for better performance
    db.detective_targets.create_index("player_id", unique=True)
    db.detective_targets.create_index("is_active")
    db.player_cache.create_index("user_id", unique=True)
    db.intelligence_notifications.create_index("timestamp")
    
    return db

# --- SMART DATA MANAGER ---
class IntelligenceDataManager:
    def __init__(self):
        self.db = init_mongodb()
        self.full_user_list = []
        self.target_families = []
        self.detective_targets = set()
        self.detailed_user_info = {}
        self.last_list_update = None
        self.lock = threading.Lock()
        self.previous_player_data = {}
        self.notification_callbacks = []

        self.load_detective_targets()

    def add_notification_callback(self, callback):
        """Register callback voor real-time notifications"""
        self.notification_callbacks.append(callback)

    def notify_intelligence_update(self, notification_data):
        """Verstuur notification naar alle registered callbacks"""
        for callback in self.notification_callbacks:
            try:
                callback(notification_data)
            except Exception as e:
                print(f"Error in notification callback: {e}")

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
        """Get all active detective targets with their latest data"""
        try:
            targets = list(self.db.detective_targets.find({"is_active": True}))
            result = []
            
            for target in targets:
                # Get latest cached data for this target
                cached_data = self.db.player_cache.find_one({"username": target['username']})
                
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
                            "shots": data.get('bullets_shot', 0),
                            "wealth": data.get('wealth', 'Unknown'),
                            "plating": data.get('plating', 'Unknown'),
                            "last_updated": cached_data.get('last_updated')
                        })
                    except:
                        pass
                
                result.append(player_info)
            
            return result
        except Exception as e:
            print(f"[ERROR] Getting detective targets: {e}")
            return []

    def cache_player_data(self, user_id, username, data):
        """Cache player data in MongoDB"""
        try:
            self.db.player_cache.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "username": username,
                        "data": json.dumps(data),
                        "last_updated": datetime.utcnow(),
                        "priority": 1
                    }
                },
                upsert=True
            )
        except Exception as e:
            print(f"[ERROR] Caching player data for {username}: {e}")

    def get_cached_players_count(self):
        """Get count of cached players"""
        try:
            return self.db.player_cache.count_documents({})
        except:
            return 0

    def add_intelligence_notification(self, player_id, username, notification_type, message, data=None):
        """Add intelligence notification to MongoDB"""
        try:
            self.db.intelligence_notifications.insert_one({
                "player_id": player_id,
                "username": username,
                "notification_type": notification_type,
                "message": message,
                "data": json.dumps(data) if data else None,
                "timestamp": datetime.utcnow(),
                "is_read": False
            })
            
            # Also notify via callbacks for real-time updates
            notification_data = {
                "type": notification_type,
                "username": username,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.notify_intelligence_update(notification_data)
            
        except Exception as e:
            print(f"[ERROR] Adding notification: {e}")

    def get_all_players(self):
        """Get all players from cache"""
        try:
            players = list(self.db.player_cache.find({}, {"_id": 0}))
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
            return formatted_players
        except Exception as e:
            print(f"[ERROR] Getting all players: {e}")
            return []

    def get_notifications(self):
        """Get recent intelligence notifications"""
        try:
            notifications = list(self.db.intelligence_notifications.find(
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
            return formatted_notifications
        except Exception as e:
            print(f"[ERROR] Getting notifications: {e}")
            return []

    def get_player_details(self, player_id):
        """Get detailed player information"""
        try:
            player = self.db.player_cache.find_one({"user_id": player_id}, {"_id": 0})
            if not player:
                return None
            
            # Return detailed player data
            return {
                "id": player.get("user_id"),
                "username": player.get("username"),
                "family_name": player.get("family_name"),
                "rank_name": player.get("rank_name"),
                "position": player.get("position", 0),
                "status": player.get("status", 1),
                "kills": player.get("kills", 0),
                "bullets_shot": player.get("bullets_shot", {"total": 0}),
                "wealth": player.get("wealth", 0),
                "plating": player.get("plating", "Unknown"),
                "last_updated": player.get("last_updated")
            }
        except Exception as e:
            print(f"[ERROR] Getting player details for {player_id}: {e}")
            return None

# --- BROWSER SETUP (Optimized for headless) ---
def setup_browser_session(driver, url, worker_name):
    """Setup browser session with Cloudflare bypass"""
    try:
        print(f"[{worker_name}] Loading page: {url}")
        driver.get(url)
        
        # Wait a bit for page to load
        time.sleep(3)
        
        # Check if we can access the API
        page_source = driver.page_source
        if "Cloudflare" in page_source or "Just a moment" in page_source:
            print(f"[{worker_name}] Cloudflare detected, waiting...")
            time.sleep(10)  # Wait for Cloudflare to resolve
        
        if "API" in page_source or "users" in page_source:
            print(f"[{worker_name}] Successfully loaded API page")
        else:
            print(f"[{worker_name}] Warning: API page might not be loaded correctly")
            
    except Exception as e:
        print(f"[{worker_name}] Browser setup error: {e}")

# --- Flask App Setup ---
app = Flask(__name__)
data_manager = IntelligenceDataManager()
priority_queue = PriorityQueue()

@app.route('/api/scraping/status')
def get_status():
    """Get scraping service status"""
    try:
        return jsonify({
            "status": "online",
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

@app.route('/api/scraping/players')
def get_players():
    """Get all players from cache"""
    try:
        players = data_manager.get_all_players()
        return jsonify({
            "players": players,
            "count": len(players),
            "last_updated": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/notifications')
def get_notifications():
    """Get intelligence notifications"""
    try:
        notifications = data_manager.get_notifications()
        return jsonify({
            "notifications": notifications,
            "count": len(notifications),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/player/<player_id>')
def get_player_details(player_id):
    """Get detailed player information"""
    try:
        player_data = data_manager.get_player_details(player_id)
        if not player_data:
            return jsonify({"error": "Player not found"}), 404
        return jsonify(player_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Background Workers ---
def smart_list_worker(driver, data_manager, priority_queue):
    """Worker that fetches the main user list periodically"""
    while True:
        try:
            print(f"[LIST_WORKER] Fetching user list...")
            driver.get(USER_LIST_URL)
            time.sleep(2)
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Try to parse JSON from the page
            try:
                # Look for JSON data in the page
                if soup.text.strip().startswith('[') or soup.text.strip().startswith('{'):
                    users_data = json.loads(soup.text.strip())
                    
                    if isinstance(users_data, list):
                        data_manager.full_user_list = users_data
                        print(f"[LIST_WORKER] Updated user list: {len(users_data)} players")
                        
                        # Cache basic user data
                        for user in users_data:
                            if isinstance(user, dict) and 'user_id' in user:
                                data_manager.cache_player_data(
                                    user['user_id'], 
                                    user.get('username', ''), 
                                    user
                                )
                    else:
                        print(f"[LIST_WORKER] Unexpected data format: {type(users_data)}")
                        
            except json.JSONDecodeError as e:
                print(f"[LIST_WORKER] Failed to parse JSON: {e}")
                print(f"[LIST_WORKER] Page content preview: {soup.text[:200]}")
                
        except Exception as e:
            print(f"[LIST_WORKER] Error: {e}")
        
        time.sleep(MAIN_LIST_INTERVAL)

def batch_detail_worker(driver, data_manager, priority_queue):
    """Worker that processes detective targets in batches"""
    while True:
        try:
            if data_manager.detective_targets:
                print(f"[DETAIL_WORKER] Processing {len(data_manager.detective_targets)} detective targets...")
                
                for username in list(data_manager.detective_targets):
                    try:
                        url = USER_DETAIL_URL_TEMPLATE.format(username)
                        driver.get(url)
                        time.sleep(1)
                        
                        page_source = driver.page_source
                        soup = BeautifulSoup(page_source, 'html.parser')
                        
                        # Try to parse user detail JSON
                        if soup.text.strip().startswith('{'):
                            user_data = json.loads(soup.text.strip())
                            
                            if isinstance(user_data, dict) and user_data.get('user_id'):
                                data_manager.cache_player_data(
                                    user_data['user_id'],
                                    username,
                                    user_data
                                )
                                print(f"[DETAIL_WORKER] Updated data for {username}")
                            
                    except Exception as e:
                        print(f"[DETAIL_WORKER] Error processing {username}: {e}")
                        
            else:
                print(f"[DETAIL_WORKER] No detective targets configured")
                
        except Exception as e:
            print(f"[DETAIL_WORKER] Worker error: {e}")
            
        time.sleep(60)  # Process detective targets every minute

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    setup_complete = threading.Event()
    driver = None
    
    try:
        print("\n[SETUP] Starting MongoDB-based Omerta Intelligence Scraping Service...")
        
        # Start Flask API
        flask_thread = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False, port=5001, host='127.0.0.1'))
        flask_thread.daemon = True
        flask_thread.start()
        print("[WEB] Flask scraping API started on http://127.0.0.1:5001")

        # Setup optimized headless browser
        print("\n--- SETTING UP HEADLESS BROWSER FOR CLOUDFLARE ---")
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--headless')  # Run in headless mode for server
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Use system's Chromium binary
        options.binary_location = "/usr/bin/chromium"

        driver = uc.Chrome(options=options, driver_executable_path="/usr/bin/chromedriver")
        
        # Test basic functionality without manual intervention
        print("[BROWSER] Testing basic functionality...")
        driver.get("https://httpbin.org/json")  # Test with a simple JSON endpoint first
        time.sleep(2)
        
        test_source = driver.page_source
        if "slideshow" in test_source:  # httpbin.org/json returns JSON with "slideshow"
            print("[BROWSER] ✅ Browser working correctly")
        else:
            print("[BROWSER] ⚠️ Browser test inconclusive")

        # Signal setup complete
        setup_complete.set()

        # Start worker threads
        list_thread = threading.Thread(target=smart_list_worker, args=(driver, data_manager, priority_queue))
        list_thread.daemon = True
        list_thread.start()

        batch_thread = threading.Thread(target=batch_detail_worker, args=(driver, data_manager, priority_queue))
        batch_thread.daemon = True
        batch_thread.start()

        print(f"\n[START] MONGODB OMERTA INTELLIGENCE SCRAPING ACTIVE")
        print(f"[LIVE] Smart List Worker: Every {MAIN_LIST_INTERVAL} seconds")
        print(f"[BATCH] Detail Worker: Detective targets every 60 seconds")
        print(f"[CACHE] Using MongoDB for persistent data")
        print(f"[TARGET] Ready for FastAPI integration on port 8001")

        while True:
            time.sleep(100)

    except KeyboardInterrupt:
        print("\n\n👋 Scraping service stopped by user.")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
    finally:
        if driver:
            driver.quit()
        print("[SECURE] Browser connections closed.")