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
import random

# Load environment variables
load_dotenv()

# --- CONFIGURATIE ---
USER_LIST_URL = "https://barafranca.com/index.php?module=API&action=users"
USER_DETAIL_URL_TEMPLATE = "https://barafranca.com/index.php?module=API&action=user&name={}"
MAIN_LIST_INTERVAL = 45
MAX_CONCURRENT_TABS = 1
CACHE_DURATION = 60
BATCH_SIZE = 3

# --- MongoDB SETUP ---
def init_mongodb():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'omerta_intelligence')]
    
    print(f"[DB] Connected to MongoDB: {mongo_url}")
    print(f"[DB] Database: {db.name}")
    
    return db

# --- DATA MANAGER ---
class IntelligenceDataManager:
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
        """Get all active detective targets with their latest data"""
        try:
            targets = list(self.db.detective_targets.find({"is_active": True}))
            result = []
            
            for target in targets:
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

# --- SIMPLE BROWSER SETUP ---
def create_simple_browser():
    """Create the simplest possible browser for maximum compatibility"""
    print("[BROWSER] Setting up ULTRA-SIMPLE browser...")
    
    # Absolute minimum options
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        # Let undetected-chromedriver handle everything automatically
        driver = uc.Chrome(options=options)
        print("[BROWSER] ✅ Simple browser created successfully")
        return driver
    except Exception as e:
        print(f"[BROWSER] ❌ Browser creation failed: {e}")
        print("[BROWSER] 🔧 Trying without any options...")
        
        # Last resort: no options at all
        driver = uc.Chrome()
        print("[BROWSER] ✅ Minimal browser created")
        return driver

def simple_cloudflare_wait(driver, url, worker_name):
    """Very simple Cloudflare handling - just wait and see"""
    print(f"[{worker_name}] Going to: {url}")
    
    try:
        driver.get(url)
        print(f"[{worker_name}] Page loaded, checking for Cloudflare...")
        
        time.sleep(5)  # Wait for page to settle
        
        page_source = driver.page_source.lower()
        if "cloudflare" in page_source or "just a moment" in page_source:
            print(f"🔒 CLOUDFLARE DETECTED!")
            print(f"📋 Please wait or solve CAPTCHA in the browser window")
            print(f"⏳ Waiting 30 seconds...")
            
            for i in range(6):
                time.sleep(5)
                try:
                    current_source = driver.page_source.lower()
                    if "cloudflare" not in current_source and "just a moment" not in current_source:
                        print(f"✅ Cloudflare passed!")
                        return True
                except:
                    pass
                print(f"⏳ Still waiting... ({(i+1)*5}/30 seconds)")
            
            print(f"⏰ Continuing anyway...")
        else:
            print(f"✅ No Cloudflare detected")
        
        return True
        
    except Exception as e:
        print(f"[{worker_name}] Error: {e}")
        return False

# --- Flask App Setup ---
app = Flask(__name__)
data_manager = IntelligenceDataManager()

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

@app.route('/api/scraping/notifications')
def get_notifications():
    """Get intelligence notifications"""
    try:
        notifications = list(
            data_manager.db.intelligence_notifications
            .find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(50)
        )
        
        return jsonify({
            "notifications": notifications,
            "count": len(notifications),
            "timestamp": datetime.utcnow().isoformat()
        })
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
            .limit(2000)  # Increased limit to show more players
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
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/player/<player_id>')
def get_player_detail(player_id):
    """Get specific player details"""
    try:
        player = data_manager.db.player_cache.find_one(
            {"user_id": player_id}, 
            {"_id": 0}
        )
        
        if not player:
            return jsonify({"error": "Player not found"}), 404
        
        try:
            player_data = json.loads(player.get('data', '{}'))
            return jsonify(player_data)
        except:
            return jsonify({"error": "Invalid player data"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Background Workers ---
def simple_list_worker(driver, data_manager):
    """Simple worker for user list"""
    while True:
        try:
            print(f"\n[LIST_WORKER] Fetching player list...")
            
            if simple_cloudflare_wait(driver, USER_LIST_URL, "LIST_WORKER"):
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                try:
                    if soup.text.strip().startswith('[') or soup.text.strip().startswith('{'):
                        users_data = json.loads(soup.text.strip())
                        
                        # Handle both list and dict formats
                        if isinstance(users_data, list):
                            player_list = users_data
                            print(f"[LIST_WORKER] ✅ Got list: {len(player_list)} players")
                        elif isinstance(users_data, dict):
                            print(f"[LIST_WORKER] 📊 Got dict, keys: {list(users_data.keys())}")
                            
                            # Try to find players in dict
                            if 'users' in users_data:
                                player_list = users_data['users']
                            elif 'players' in users_data:
                                player_list = users_data['players']
                            elif 'data' in users_data:
                                player_list = users_data['data']
                            else:
                                # Extract all player-like objects
                                player_list = []
                                for key, value in users_data.items():
                                    if isinstance(value, dict) and 'user_id' in value:
                                        player_list.append(value)
                                    elif isinstance(value, list):
                                        player_list.extend(value)
                            
                            print(f"[LIST_WORKER] ✅ Extracted {len(player_list) if isinstance(player_list, list) else 0} players")
                        else:
                            print(f"[LIST_WORKER] ⚠️ Unexpected format: {type(users_data)}")
                            player_list = []
                        
                        # Cache data
                        if isinstance(player_list, list):
                            cached = 0
                            for user in player_list:
                                if isinstance(user, dict) and 'user_id' in user:
                                    data_manager.cache_player_data(
                                        user['user_id'], 
                                        user.get('username', f"Player_{user['user_id']}"), 
                                        user
                                    )
                                    cached += 1
                            print(f"[LIST_WORKER] 💾 Cached {cached} players")
                            
                except json.JSONDecodeError as e:
                    print(f"[LIST_WORKER] ❌ JSON parse error: {e}")
            else:
                print(f"[LIST_WORKER] ❌ Failed to access user list")
                
        except Exception as e:
            print(f"[LIST_WORKER] ❌ Error: {e}")
        
        print(f"[LIST_WORKER] ⏳ Next update in {MAIN_LIST_INTERVAL} seconds")
        time.sleep(MAIN_LIST_INTERVAL)

def simple_detail_worker(driver, data_manager):
    """Simple worker for detective targets"""
    while True:
        try:
            if data_manager.detective_targets:
                print(f"\n[DETAIL_WORKER] Processing {len(data_manager.detective_targets)} targets...")
                
                for username in list(data_manager.detective_targets):
                    try:
                        url = USER_DETAIL_URL_TEMPLATE.format(username)
                        print(f"[DETAIL_WORKER] Getting {username}...")
                        
                        if simple_cloudflare_wait(driver, url, "DETAIL_WORKER"):
                            page_source = driver.page_source
                            soup = BeautifulSoup(page_source, 'html.parser')
                            
                            if soup.text.strip().startswith('{'):
                                user_data = json.loads(soup.text.strip())
                                
                                if isinstance(user_data, dict) and user_data.get('user_id'):
                                    data_manager.cache_player_data(
                                        user_data['user_id'],
                                        username,
                                        user_data
                                    )
                                    print(f"[DETAIL_WORKER] ✅ Updated {username}")
                        else:
                            print(f"[DETAIL_WORKER] ❌ Failed for {username}")
                        
                        time.sleep(random.uniform(5, 10))  # Wait between requests
                        
                    except Exception as e:
                        print(f"[DETAIL_WORKER] ❌ Error with {username}: {e}")
                        
            else:
                print(f"[DETAIL_WORKER] ℹ️ No detective targets")
                
        except Exception as e:
            print(f"[DETAIL_WORKER] ❌ Worker error: {e}")
            
        print(f"[DETAIL_WORKER] ⏳ Next batch in 2 minutes")
        time.sleep(120)

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    driver = None
    
    try:
        print("\n" + "="*50)
        print("🎯 SIMPLE OMERTA SCRAPING SERVICE")
        print("🔧 Maximum Compatibility Mode")
        print("="*50)
        
        # Start Flask API
        flask_thread = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False, port=5001, host='127.0.0.1'))
        flask_thread.daemon = True
        flask_thread.start()
        print("🌐 Flask API: http://127.0.0.1:5001")

        # Setup simple browser
        driver = create_simple_browser()
        
        print("🚀 Starting workers...")

        # Start workers
        list_thread = threading.Thread(target=simple_list_worker, args=(driver, data_manager))
        list_thread.daemon = True
        list_thread.start()

        detail_thread = threading.Thread(target=simple_detail_worker, args=(driver, data_manager))
        detail_thread.daemon = True
        detail_thread.start()

        print("\n" + "="*50)
        print("✅ SIMPLE SCRAPING ACTIVE")
        print("📱 List Worker: Every 45 seconds") 
        print("🎯 Detail Worker: Every 2 minutes")
        print("💾 Database: MongoDB")
        print("🌐 Browser: Simple Chrome")
        print("\n💡 TIP: Manually help with Cloudflare!")
        print("🛑 Ctrl+C to stop")
        print("="*50)

        while True:
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n\n👋 Simple scraper stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if driver:
            driver.quit()
        print("🔒 Browser closed")