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

# --- SIMPLE BROWSER SETUP ---
def create_simple_browser():
    """Create a simple visible browser"""
    print("[BROWSER] Setting up simple visible browser...")
    
    options = uc.ChromeOptions()
    
    # Basic options
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    
    # Anti-detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agent
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Window size
    options.add_argument('--window-size=1280,720')
    
    # Create driver
    driver = uc.Chrome(options=options, version_main=None)
    
    # Hide automation indicators
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    print("[BROWSER] ✅ Browser ready")
    return driver

def handle_cloudflare(driver, url, timeout=60):
    """Handle Cloudflare with user guidance"""
    print(f"\n[CLOUDFLARE] Navigating to: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)
        
        page_source = driver.page_source.lower()
        
        if "cloudflare" in page_source or "just a moment" in page_source or "checking your browser" in page_source:
            print(f"\n🔒 CLOUDFLARE GEDETECTEERD!")
            print(f"📋 ACTIES NODIG:")
            print(f"   1. ✅ Chrome venster is zichtbaar")
            print(f"   2. ⏳ Wacht 5-10 seconden voor automatische bypass")
            print(f"   3. 🧩 Los CAPTCHA op als die verschijnt")
            print(f"   4. 🚪 Laat het venster OPEN")
            print(f"\n⏰ Maximaal {timeout} seconden wachttijd...")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    current_source = driver.page_source.lower()
                    if "cloudflare" not in current_source and "just a moment" not in current_source:
                        print(f"\n✅ CLOUDFLARE GEPASSEERD! Scraper gaat verder...")
                        return True
                except:
                    pass
                
                time.sleep(2)
                elapsed = int(time.time() - start_time)
                if elapsed % 10 == 0 and elapsed > 0:
                    print(f"⏳ {timeout - elapsed} seconden over...")
            
            print(f"⏰ Time-out bereikt. Proberen verder te gaan...")
            return False
        else:
            print(f"✅ Geen Cloudflare - direct toegang!")
            return True
            
    except Exception as e:
        print(f"[CLOUDFLARE] Fout: {e}")
        return False

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

# --- Background Workers ---
def simple_list_worker(driver, data_manager):
    """Simple worker for user list"""
    while True:
        try:
            print(f"\n[LIST_WORKER] Fetching player list...")
            
            if handle_cloudflare(driver, USER_LIST_URL):
                time.sleep(2)  # Extra wait after Cloudflare
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                try:
                    if soup.text.strip().startswith('[') or soup.text.strip().startswith('{'):
                        users_data = json.loads(soup.text.strip())
                        
                        if isinstance(users_data, list):
                            data_manager.full_user_list = users_data
                            print(f"[LIST_WORKER] ✅ Updated: {len(users_data)} players")
                            
                            # Cache data
                            for user in users_data:
                                if isinstance(user, dict) and 'user_id' in user:
                                    data_manager.cache_player_data(
                                        user['user_id'], 
                                        user.get('username', ''), 
                                        user
                                    )
                        else:
                            print(f"[LIST_WORKER] ⚠️ Unexpected data: {type(users_data)}")
                            
                except json.JSONDecodeError as e:
                    print(f"[LIST_WORKER] ❌ JSON error: {e}")
                    print(f"Page preview: {soup.text[:200]}")
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
                        
                        if handle_cloudflare(driver, url, timeout=30):
                            time.sleep(1)
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
                            print(f"[DETAIL_WORKER] ❌ Failed to access {username}")
                        
                        # Wait between requests
                        time.sleep(random.uniform(3, 6))
                        
                    except Exception as e:
                        print(f"[DETAIL_WORKER] ❌ Error with {username}: {e}")
                        
            else:
                print(f"[DETAIL_WORKER] ℹ️ No detective targets")
                
        except Exception as e:
            print(f"[DETAIL_WORKER] ❌ Worker error: {e}")
            
        print(f"[DETAIL_WORKER] ⏳ Next batch in 90 seconds")
        time.sleep(90)

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    driver = None
    
    try:
        print("\n" + "="*60)
        print("🎯 OMERTA INTELLIGENCE SCRAPING SERVICE")
        print("📍 Direct Barafranca Access - No Tests")
        print("="*60)
        
        # Start Flask API
        flask_thread = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False, port=5001, host='127.0.0.1'))
        flask_thread.daemon = True
        flask_thread.start()
        print("🌐 Flask API: http://127.0.0.1:5001")

        # Setup browser
        driver = create_simple_browser()
        
        print("🚀 Starting background workers...")

        # Start workers
        list_thread = threading.Thread(target=simple_list_worker, args=(driver, data_manager))
        list_thread.daemon = True
        list_thread.start()

        detail_thread = threading.Thread(target=simple_detail_worker, args=(driver, data_manager))
        detail_thread.daemon = True
        detail_thread.start()

        print("\n" + "="*60)
        print("✅ OMERTA SCRAPING ACTIVE")
        print("📱 List Worker: Every 45 seconds") 
        print("🎯 Detail Worker: Every 90 seconds")
        print("💾 Database: MongoDB")
        print("🌐 Browser: Visible Chrome window")
        print("\n💡 TIP: Help met Cloudflare als het vraagt!")
        print("🛑 Ctrl+C om te stoppen")
        print("="*60)

        while True:
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n\n👋 Scraper gestopt door gebruiker")
    except Exception as e:
        print(f"\n❌ Fout: {e}")
    finally:
        if driver:
            driver.quit()
        print("🔒 Browser gesloten")