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
MAIN_LIST_INTERVAL = 45  # Langer interval
MAX_CONCURRENT_TABS = 1  # Minder concurrent tabs
CACHE_DURATION = 60  # Langer cache
BATCH_SIZE = 3  # Kleinere batches

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

# --- STEALTH BROWSER SETUP ---
def create_stealth_browser():
    """Create a stealth browser with anti-detection measures"""
    print("[STEALTH] Setting up anti-detection browser...")
    
    # Random user agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ]
    
    options = uc.ChromeOptions()
    
    # Basic stealth options
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-first-run')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-infobars')
    
    # Anti-detection measures
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-ipc-flooding-protection')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Random user agent
    selected_ua = random.choice(user_agents)
    options.add_argument(f'--user-agent={selected_ua}')
    print(f"[STEALTH] Using User Agent: {selected_ua}")
    
    # Window size
    options.add_argument('--window-size=1366,768')
    
    # Create driver with version_main for compatibility
    driver = uc.Chrome(options=options, version_main=None)
    
    # Execute JavaScript to hide automation indicators
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def smart_cloudflare_bypass(driver, url, max_attempts=3):
    """Smart Cloudflare bypass with multiple strategies"""
    
    for attempt in range(max_attempts):
        print(f"\n[BYPASS] Poging {attempt + 1}/{max_attempts} voor {url}")
        
        try:
            # Random delay before request
            delay = random.uniform(2, 5)
            print(f"[BYPASS] Wachten {delay:.1f} seconden...")
            time.sleep(delay)
            
            driver.get(url)
            
            # Wait for initial page load
            time.sleep(3)
            
            page_source = driver.page_source.lower()
            
            if "cloudflare" in page_source or "just a moment" in page_source or "checking your browser" in page_source:
                print(f"🔒 CLOUDFLARE GEDETECTEERD op poging {attempt + 1}")
                
                if attempt == 0:
                    print(f"📋 AUTOMATISCHE BYPASS PROBEREN...")
                    # Try automatic bypass
                    time.sleep(10)  # Wait longer
                    
                    # Refresh the page
                    driver.refresh()
                    time.sleep(5)
                    
                    page_source = driver.page_source.lower()
                    
                    if "cloudflare" not in page_source:
                        print(f"✅ Automatische bypass succesvol!")
                        return True
                
                # Manual intervention needed
                if attempt >= 1:
                    print(f"\n🔒 HANDMATIGE INTERVENTIE NODIG!")
                    print(f"📋 INSTRUCTIES:")
                    print(f"   1. Chrome browser venster is zichtbaar")
                    print(f"   2. Los eventuele CAPTCHA op")
                    print(f"   3. Wacht tot de pagina laadt")
                    print(f"   4. Laat browser venster open")
                    print(f"\n⏳ Wachten tot je klaar bent (60 seconden)...")
                    
                    # Wait for manual intervention
                    for i in range(60):
                        time.sleep(1)
                        try:
                            current_source = driver.page_source.lower()
                            if "cloudflare" not in current_source and "just a moment" not in current_source:
                                print(f"\n✅ HANDMATIGE BYPASS SUCCESVOL!")
                                return True
                        except:
                            pass
                        
                        if i % 10 == 0 and i > 0:
                            print(f"⏳ Nog {60-i} seconden...")
                
            else:
                # Success - no Cloudflare detected
                print(f"✅ Pagina toegankelijk - geen Cloudflare!")
                return True
            
        except Exception as e:
            print(f"[BYPASS] Fout op poging {attempt + 1}: {e}")
            
        # Wait before retry
        if attempt < max_attempts - 1:
            wait_time = (attempt + 1) * 10
            print(f"⏳ Wachten {wait_time} seconden voor volgende poging...")
            time.sleep(wait_time)
    
    print(f"❌ Cloudflare bypass gefaald na {max_attempts} pogingen")
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
def smart_list_worker(driver, data_manager, priority_queue):
    """Worker that fetches the main user list periodically with stealth"""
    while True:
        try:
            print(f"[LIST_WORKER] Fetching user list (stealth mode)...")
            
            if smart_cloudflare_bypass(driver, USER_LIST_URL):
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Try to parse JSON from the page
                try:
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
            else:
                print(f"[LIST_WORKER] Failed to bypass Cloudflare for user list")
                
        except Exception as e:
            print(f"[LIST_WORKER] Error: {e}")
        
        # Random interval to avoid detection
        interval = random.uniform(MAIN_LIST_INTERVAL, MAIN_LIST_INTERVAL + 15)
        print(f"[LIST_WORKER] Next update in {interval:.1f} seconds")
        time.sleep(interval)

def batch_detail_worker(driver, data_manager, priority_queue):
    """Worker that processes detective targets with stealth"""
    while True:
        try:
            if data_manager.detective_targets:
                print(f"[DETAIL_WORKER] Processing {len(data_manager.detective_targets)} detective targets (stealth)...")
                
                for username in list(data_manager.detective_targets):
                    try:
                        url = USER_DETAIL_URL_TEMPLATE.format(username)
                        
                        if smart_cloudflare_bypass(driver, url):
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
                        else:
                            print(f"[DETAIL_WORKER] Failed to bypass Cloudflare for {username}")
                        
                        # Random delay between requests
                        delay = random.uniform(3, 8)
                        time.sleep(delay)
                        
                    except Exception as e:
                        print(f"[DETAIL_WORKER] Error processing {username}: {e}")
                        
            else:
                print(f"[DETAIL_WORKER] No detective targets configured")
                
        except Exception as e:
            print(f"[DETAIL_WORKER] Worker error: {e}")
            
        # Longer interval for stealth
        interval = random.uniform(90, 120)
        print(f"[DETAIL_WORKER] Next batch in {interval:.1f} seconds")
        time.sleep(interval)

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    setup_complete = threading.Event()
    driver = None
    
    try:
        print("\n[SETUP] Starting STEALTH MongoDB Omerta Intelligence Scraping Service...")
        print("🥷 STEALTH MODE: Advanced anti-detection measures")
        print("🔄 CLOUDFLARE BYPASS: Intelligent retry with manual fallback")
        
        # Start Flask API
        flask_thread = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False, port=5001, host='127.0.0.1'))
        flask_thread.daemon = True
        flask_thread.start()
        print("[WEB] Flask scraping API started on http://127.0.0.1:5001")

        # Setup stealth browser
        driver = create_stealth_browser()
        
        # Browser ready - no test needed
        print("[BROWSER] ✅ Stealth browser ready voor Barafranca")

        # Signal setup complete
        setup_complete.set()

        # Start worker threads
        list_thread = threading.Thread(target=smart_list_worker, args=(driver, data_manager, priority_queue))
        list_thread.daemon = True
        list_thread.start()

        batch_thread = threading.Thread(target=batch_detail_worker, args=(driver, data_manager, priority_queue))
        batch_thread.daemon = True
        batch_thread.start()

        print(f"\n[START] STEALTH OMERTA INTELLIGENCE SCRAPING ACTIVE")
        print(f"🥷 Anti-detection measures active")
        print(f"🔄 Smart Cloudflare bypass enabled")
        print(f"[LIVE] Smart List Worker: Every 45-60 seconds")
        print(f"[BATCH] Detail Worker: Every 90-120 seconds")
        print(f"[CACHE] Using MongoDB for persistent data")
        print(f"💡 TIP: Laat Chrome venster open en help bij CAPTCHA's!")

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