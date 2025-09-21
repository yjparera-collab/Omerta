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
import random  # Added for random delays

# Load environment variables
load_dotenv()

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
    db.detective_targets.create_index("username", unique=True)  # Changed to username
    db.detective_targets.create_index("is_active")
    db.player_cache.create_index("username", unique=True)  # Changed to username
    db.player_cache.create_index("user_id")  # Keep as secondary index
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

    def get_user_id_by_username(self, username: str):
        """Try to resolve user_id from username using latest list or cache"""
        if not username:
            return None
        try:
            name_l = username.lower()
            # Prefer the most recent full_user_list
            for user in self.full_user_list or []:
                # different list formats may use different keys
                u_name = user.get('username') or user.get('uname') or user.get('name')
                if u_name and str(u_name).lower() == name_l:
                    uid = user.get('user_id') or user.get('id') or user.get('player_id')
                    if uid is not None:
                        return str(uid)
            # Fallback to player_cache document
            doc = self.db.player_cache.find_one({"username": username})
            if doc and doc.get('user_id'):
                return str(doc['user_id'])
        except Exception as e:
            print(f"[MAP] Failed to map username to user_id for {username}: {e}")
        return None

    def notify_backend_list_updated(self, payload=None):
        """Non-blocking notify to FastAPI to broadcast updates"""
        try:
            backend_url = os.environ.get('BACKEND_URL', 'http://127.0.0.1:8001')
            data = payload or {"source": "scraper", "timestamp": datetime.utcnow().isoformat()}
            # fire-and-forget with short timeout
            requests.post(f"{backend_url}/api/internal/list-updated", json=data, timeout=2)
        except Exception as e:
            # don't crash scraper because backend might not be local
            if 'ConnectionRefusedError' not in str(e):
                print(f"[NOTIFY] Backend notify failed: {e}")

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
            
            # Try to resolve user_id if missing
            if not user_id_str:
                user_id_str = self.get_user_id_by_username(username_str)
            
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

# --- IMPROVED BROWSER SETUP (Windows - VISIBLE with ANTI-DETECTION) ---
def create_compatible_browser():
    """Create compatible browser for Windows with fallback options"""
    print("[BROWSER] Setting up compatible browser voor Windows...")
    
    options = uc.ChromeOptions()
    
    # Basic required options (compatible with all Chrome versions)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-first-run')
    options.add_argument('--disable-default-apps')
    
    # User agent
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Window size
    options.add_argument('--window-size=1280,720')
    
    # Try experimental options with fallback
    try:
        # Advanced anti-detection (may not work on all Chrome versions)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        print("[BROWSER] ✅ Advanced anti-detection options applied")
    except Exception as e:
        print(f"[BROWSER] ⚠️ Advanced options not supported: {e}")
        print("[BROWSER] ℹ️ Using basic compatibility mode")
    
    try:
        # Create driver with automatic version detection
        driver = uc.Chrome(options=options)
        print("[BROWSER] ✅ Chrome driver created successfully")
        
        # Try to hide automation indicators
        try:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("[BROWSER] ✅ Webdriver masking applied")
        except Exception as e:
            print(f"[BROWSER] ⚠️ Webdriver masking failed: {e}")
        
        return driver
        
    except Exception as e:
        print(f"[BROWSER] ❌ Chrome driver creation failed: {e}")
        print("[BROWSER] 🔧 Trying fallback options...")
        
        # Fallback: Ultra-simple options
        simple_options = uc.ChromeOptions()
        simple_options.add_argument('--no-sandbox')
        simple_options.add_argument('--disable-dev-shm-usage')
        simple_options.add_argument('--window-size=1280,720')
        
        driver = uc.Chrome(options=simple_options)
        print("[BROWSER] ✅ Fallback browser created")
        return driver

def smart_cloudflare_handler(driver, url, worker_name, timeout=60):
    """Smart Cloudflare handler with improved detection (from working version)"""
    print(f"\n[{worker_name}] Navigating to: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)  # Initial wait
        
        page_source = driver.page_source.lower()
        
        # IMPROVED: Better Cloudflare detection (from working version)
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
                    # IMPROVED: Better detection logic (from working version)
                    if "cloudflare" not in current_source and "just a moment" not in current_source and "checking your browser" not in current_source:
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
        print(f"[{worker_name}] Cloudflare handler error: {e}")
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

@app.route('/api/scraping/notifications')
def get_notifications():
    """Get intelligence notifications"""
    try:
        # Get recent notifications from MongoDB
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
        # Get all cached players from MongoDB
        players = list(
            data_manager.db.player_cache
            .find({}, {"_id": 0})
            .sort("last_updated", -1)
            .limit(2000)  # Increased limit to show more players
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
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/player/<player_id>')
def get_player_detail(player_id):
    """Get specific player details by user_id (legacy support)"""
    try:
        # Find player in cache by user_id
        player = data_manager.db.player_cache.find_one(
            {"user_id": player_id}, 
            {"_id": 0}
        )
        
        if not player:
            return jsonify({"error": "Player not found"}), 404
        
        # Parse player data
        try:
            player_data = json.loads(player.get('data', '{}'))
            return jsonify(player_data)
        except:
            return jsonify({"error": "Invalid player data"}), 500
            
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

# --- Background Workers ---
def smart_list_worker(driver, data_manager, priority_queue):
    """Worker that fetches the main user list with improved Cloudflare handling"""
    while True:
        try:
            print(f"\n[LIST_WORKER] Fetching user list...")
            
            # Use improved Cloudflare handler
            if smart_cloudflare_handler(driver, USER_LIST_URL, worker_name="LIST_WORKER"):
                time.sleep(2)  # Extra wait after Cloudflare
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Try to parse JSON from the page
                try:
                    # Look for JSON data in the page
                    if soup.text.strip().startswith('[') or soup.text.strip().startswith('{'):
                        users_data = json.loads(soup.text.strip())
                        
                        # Handle both list and dict formats
                        if isinstance(users_data, list):
                            # Direct list of players
                            player_list = users_data
                            print(f"[LIST_WORKER] ✅ Got list format: {len(player_list)} players")
                        elif isinstance(users_data, dict):
                            # Dictionary wrapper or container
                            print(f"[LIST_WORKER] 📊 Got dict format, keys: {list(users_data.keys())}")

                            # Unwrap common wrapper {cached, time, expires, data}
                            container = users_data.get('data', users_data)

                            # If the unwrapped container is a list, it's the player list
                            if isinstance(container, list):
                                player_list = container
                            elif isinstance(container, dict):
                                # Try common keys inside container
                                if 'users' in container:
                                    player_list = container['users']
                                elif 'players' in container:
                                    player_list = container['players']
                                else:
                                    # Extract dict values that look like player dicts
                                    player_list = []
                                    for key, value in container.items():
                                        if isinstance(value, dict) and ('user_id' in value or 'id' in value):
                                            player_list.append(value)
                                        elif isinstance(value, list):
                                            player_list.extend(value)
                            else:
                                player_list = []

                            print(f"[LIST_WORKER] ✅ Extracted {len(player_list) if isinstance(player_list, list) else 0} players from wrapper")
                        else:
                            print(f"[LIST_WORKER] ⚠️ Unexpected data format: {type(users_data)}")
                            player_list = []
                        
                        # Process the player list
                        if isinstance(player_list, list) and len(player_list) > 0:
                            data_manager.full_user_list = player_list
                            print(f"[LIST_WORKER] ✅ Updated user list: {len(player_list)} players")
                            
                            # Cache basic user data - USERNAME FIRST approach
                            cached_count = 0
                            failed_count = 0
                            
                            # Debug: Check first player structure
                            if len(player_list) > 0:
                                first_player = player_list[0]
                                print(f"[LIST_WORKER] 🔍 First player keys: {list(first_player.keys()) if isinstance(first_player, dict) else 'Not a dict'}")
                                print(f"[LIST_WORKER] 🔍 First player sample: {str(first_player)[:200]}...")
                            
                            for user in player_list:
                                if isinstance(user, dict):
                                    # Try different ID field names
                                    user_id = None
                                    username = None
                                    
                                    # Common ID field names
                                    for id_field in ['user_id', 'id', 'player_id', 'userId', 'playerId']:
                                        if id_field in user:
                                            user_id = user[id_field]
                                            break
                                    
                                    # Common username field names
                                    for name_field in ['username', 'name', 'player_name', 'userName', 'playerName', 'uname']:
                                        if name_field in user:
                                            username = user[name_field]
                                            break
                                    
                                    if user_id is None:
                                        # Try to backfill from common fields
                                        user_id = user.get('id') or user.get('player_id')

                                    # USERNAME FIRST: Require username, user_id optional
                                    if username:
                                        try:
                                            # Normalize to unified structure used by UI: id/uname/rank/plating/position
                                            normalized = {
                                                "id": str(user_id) if user_id else None,
                                                "user_id": str(user_id) if user_id else None,
                                                "uname": username,
                                                "username": username,  # Ensure both keys
                                                "rank_name": user.get('rank_name') or user.get('rank'),
                                                "plating": user.get('plating'),
                                                "position": user.get('position'),
                                                "status": user.get('status'),
                                                "f_name": user.get('f_name') or (user.get('family', {}) or {}).get('name'),
                                            }
                                            # USERNAME FIRST caching
                                            data_manager.cache_player_data(
                                                user_id,  # Can be None
                                                username,  # Primary key
                                                normalized
                                            )
                                            cached_count += 1
                                        except Exception as e:
                                            print(f"[LIST_WORKER] ❌ Cache error for {username}: {e}")
                                            failed_count += 1
                                    else:
                                        failed_count += 1
                                        if failed_count <= 3:  # Only show first few failures
                                            print(f"[LIST_WORKER] ⚠️ No username found in player keys: {list(user.keys())}")
                            
                            print(f"[LIST_WORKER] 💾 Cached {cached_count} players, {failed_count} failed")
                        else:
                            print(f"[LIST_WORKER] ❌ No valid player data found")
                            
                except json.JSONDecodeError as e:
                    print(f"[LIST_WORKER] ❌ Failed to parse JSON: {e}")
                    print(f"[LIST_WORKER] Page content preview: {soup.text[:200]}")
            else:
                print(f"[LIST_WORKER] ❌ Failed to bypass Cloudflare")
                
        except Exception as e:
            print(f"[LIST_WORKER] ❌ Error: {e}")
        
        print(f"[LIST_WORKER] ⏳ Next update in {MAIN_LIST_INTERVAL} seconds")
        time.sleep(MAIN_LIST_INTERVAL)

def batch_detail_worker(driver, data_manager, priority_queue):
    """Worker that processes detective targets with improved Cloudflare handling - USERNAME FIRST"""
    while True:
        try:
            if data_manager.detective_targets:
                print(f"\n[DETAIL_WORKER] Processing {len(data_manager.detective_targets)} detective targets...")
                
                for username in list(data_manager.detective_targets):
                    try:
                        url = USER_DETAIL_URL_TEMPLATE.format(username)
                        print(f"[DETAIL_WORKER] Getting {username}...")
                        
                        # Use improved Cloudflare handler
                        if smart_cloudflare_handler(driver, url, worker_name="DETAIL_WORKER", timeout=30):
                            time.sleep(1)  # Brief wait after Cloudflare
                            page_source = driver.page_source
                            soup = BeautifulSoup(page_source, 'html.parser')
                            
                            # Try to parse user detail JSON
                            if soup.text.strip().startswith('{'):
                                user_data = json.loads(soup.text.strip())

                                if isinstance(user_data, dict):
                                    # Unwrap wrapper if present {"cached":..., "data":{...}}
                                    inner = user_data.get('data', user_data)
                                    
                                    # Ensure user_id by mapping if missing
                                    uid = user_data.get('user_id') or inner.get('user_id')
                                    if not uid:
                                        uid = data_manager.get_user_id_by_username(username)
                                        if uid:
                                            inner['user_id'] = uid
                                    
                                    # USERNAME FIRST caching - username is required, user_id optional
                                    data_manager.cache_player_data(
                                        uid,        # Can be None
                                        username,   # PRIMARY KEY
                                        inner
                                    )
                                    print(f"[DETAIL_WORKER] ✅ Updated data for {username} (id={uid})")
                                    
                                    # Notify backend for real-time updates
                                    data_manager.notify_backend_list_updated({
                                        "username": username, 
                                        "user_id": str(uid) if uid else None
                                    })
                                    
                        else:
                            print(f"[DETAIL_WORKER] ❌ Failed to access {username}")
                        
                        # Random delay between requests to avoid detection
                        delay = random.uniform(3, 6)
                        time.sleep(delay)
                            
                    except Exception as e:
                        print(f"[DETAIL_WORKER] ❌ Error processing {username}: {e}")
                        
            else:
                print(f"[DETAIL_WORKER] ℹ️ No detective targets configured")
                
        except Exception as e:
            print(f"[DETAIL_WORKER] ❌ Worker error: {e}")
            
        print(f"[DETAIL_WORKER] ⏳ Next batch in 90 seconds")
        time.sleep(90)  # Longer interval for stealth

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    setup_complete = threading.Event()
    driver = None
    
    try:
        print("\n[SETUP] Starting MongoDB-based Omerta Intelligence Scraping Service (Windows)...")
        print("🪟 WINDOWS MODE: Browser zal ZICHTBAAR zijn voor Cloudflare bypass")
        
        # Start Flask API
        flask_thread = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False, port=5001, host='127.0.0.1'))
        flask_thread.daemon = True
        flask_thread.start()
        print("[WEB] Flask scraping API started on http://127.0.0.1:5001")

        # Setup VISIBLE compatible browser for Windows
        print("\n--- SETTING UP COMPATIBLE BROWSER FOR CLOUDFLARE ---")
        driver = create_compatible_browser()
        
        print("[BROWSER] ✅ Ready to bypass Cloudflare - browser is VISIBLE")

        # Signal setup complete
        setup_complete.set()

        # Start worker threads
        list_thread = threading.Thread(target=smart_list_worker, args=(driver, data_manager, priority_queue))
        list_thread.daemon = True
        list_thread.start()

        batch_thread = threading.Thread(target=batch_detail_worker, args=(driver, data_manager, priority_queue))
        batch_thread.daemon = True
        batch_thread.start()

        print(f"\n" + "="*60)
        print(f"🎯 MONGODB OMERTA INTELLIGENCE SCRAPING ACTIVE (WINDOWS)")
        print(f"🛡️  ANTI-DETECTION BROWSER: Advanced Cloudflare bypass")
        print(f"🪟 Chrome browser venster is ZICHTBAAR voor handmatige hulp")
        print(f"[LIVE] Smart List Worker: Every {MAIN_LIST_INTERVAL} seconds")
        print(f"[BATCH] Detail Worker: Detective targets every 90 seconds")
        print(f"[CACHE] Using MongoDB for persistent data - USERNAME FIRST")
        print(f"[TARGET] Ready for FastAPI integration on port 8001")
        print(f"\n💡 TIP: Laat het Chrome venster open - automatische bypass actief!")
        print(f"🔧 HELP: Los CAPTCHA's op als die verschijnen")
        print(f"🛑 STOP: Ctrl+C om te stoppen")
        print(f"="*60)

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