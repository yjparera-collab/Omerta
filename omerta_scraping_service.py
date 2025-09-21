#!/usr/bin/env python3
"""
Omerta Intelligence Scraping Service - Production Ready
Username-first Cloudflare bypass using undetected-chromedriver
"""

import time
from datetime import datetime
import json
import threading
from flask import Flask, request, jsonify
import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys

# Load environment variables
load_dotenv()

# --- CONFIGURATIE ---
USER_LIST_URL = "https://barafranca.com/index.php?module=API&action=users"
USER_DETAIL_URL_TEMPLATE = "https://barafranca.com/index.php?module=API&action=user&name={}"
MAIN_LIST_INTERVAL = 30
DETAIL_BATCH_INTERVAL = 90
MAX_RETRIES = 3

# --- MongoDB SETUP ---
def init_mongodb():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = MongoClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'omerta_intelligence')]
    
    print(f"[DB] Connected to MongoDB: {mongo_url}")
    print(f"[DB] Database: {db.name}")
    
    # Create indexes gracefully
    try:
        db.detective_targets.create_index("username", unique=True)
        db.detective_targets.create_index("is_active")
        db.player_cache.create_index("username", unique=True)
        db.intelligence_notifications.create_index("timestamp")
        print("[DB] Index setup completed")
    except Exception as e:
        print(f"[DB] Index setup issue (likely already exists): {e}")
    
    return db

# --- ADVANCED SELENIUM SETUP ---
def create_stealth_browser():
    """Create undetectable browser for Cloudflare bypass"""
    print("[BROWSER] Setting up advanced Cloudflare bypass browser...")

    options = Options()
    
    # Essential stealth options
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-first-run')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-features=VizDisplayCompositor')
    
    # Anti-detection measures
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    
    # Container compatibility
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')
    
    # Use system Chromium
    service = Service('/usr/bin/chromedriver')
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        
        # Execute stealth script to hide automation
        stealth_script = """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        window.chrome = {runtime: {}};
        Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})});
        """
        driver.execute_script(stealth_script)
        
        print("[BROWSER] ✅ Stealth browser created successfully")
        return driver
        
    except Exception as e:
        print(f"[BROWSER] ❌ Failed to create browser: {e}")
        return None

def bypass_cloudflare_and_get_json(driver, url, timeout=60):
    """Advanced Cloudflare bypass with JSON extraction"""
    print(f"[CLOUDFLARE] Accessing: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)
        
        page_source = driver.page_source.lower()
        
        # Check for Cloudflare protection
        if any(indicator in page_source for indicator in ["cloudflare", "just a moment", "checking your browser"]):
            print(f"🔒 CLOUDFLARE DETECTED! Waiting for bypass...")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    current_source = driver.page_source.lower()
                    if not any(indicator in current_source for indicator in ["cloudflare", "just a moment", "checking your browser"]):
                        print(f"✅ CLOUDFLARE BYPASSED!")
                        break
                except:
                    pass
                time.sleep(2)
            else:
                print(f"⏰ Cloudflare bypass timeout")
                return None
        
        # Extract JSON data
        try:
            page_content = driver.page_source
            
            # Look for JSON in page body or pre tags
            if '<pre>' in page_content and '</pre>' in page_content:
                json_start = page_content.find('<pre>') + 5
                json_end = page_content.find('</pre>')
                json_text = page_content[json_start:json_end].strip()
            else:
                # Try to find JSON in body text
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page_content, 'html.parser')
                json_text = soup.get_text().strip()
            
            # Parse JSON
            if json_text.startswith('{') or json_text.startswith('['):
                data = json.loads(json_text)
                print(f"[SUCCESS] Retrieved JSON data from {url}")
                return data
            else:
                print(f"[ERROR] No JSON found in response from {url}")
                return None
                
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parsing failed for {url}: {e}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Browser error for {url}: {e}")
        return None

# --- DATA MANAGER ---
class OmertaIntelligenceManager:
    def __init__(self):
        self.db = init_mongodb()
        self.detective_targets = set()
        self.browser = None
        self.lock = threading.Lock()
        self.load_detective_targets()
        
    def init_browser(self):
        """Initialize browser when needed"""
        if not self.browser:
            self.browser = create_stealth_browser()
        return self.browser is not None

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

    def cache_player_data(self, username, data, user_id=None):
        """Cache player data using username as primary key"""
        try:
            username_str = str(username) if username else None
            if not username_str:
                print("[CACHE] ❌ No username provided")
                return False
            
            doc = {
                "username": username_str,
                "user_id": str(user_id) if user_id else None,
                "data": json.dumps(data, default=str),
                "last_updated": datetime.utcnow(),
                "priority": 1
            }
            
            result = self.db.player_cache.update_one(
                {"username": username_str},
                {"$set": doc},
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                print(f"[CACHE] ✅ Cached data for {username_str}")
                return True
            else:
                print(f"[CACHE] ⚠️ No changes for {username_str}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Caching failed for {username}: {e}")
            return False

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
                        
                        # Handle data wrapper if present
                        inner = raw.get('data', raw) if isinstance(raw, dict) and 'data' in raw else raw
                        
                        # Extract stats safely
                        if isinstance(inner, dict):
                            if inner.get('kills') is not None:
                                player_info["kills"] = inner.get('kills')
                            
                            # Handle bullets_shot
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

    def notify_backend_update(self, data=None):
        """Notify backend of data updates"""
        try:
            backend_url = os.environ.get('BACKEND_URL', 'http://127.0.0.1:8001')
            payload = data or {"source": "scraper", "timestamp": datetime.utcnow().isoformat()}
            requests.post(f"{backend_url}/api/internal/list-updated", json=payload, timeout=2)
        except Exception as e:
            if 'ConnectionRefusedError' not in str(e):
                print(f"[NOTIFY] Backend notify failed: {e}")

# --- FLASK APP ---
app = Flask(__name__)
data_manager = OmertaIntelligenceManager()

@app.route('/api/scraping/status')
def get_status():
    """Get scraping service status"""
    try:
        return jsonify({
            "status": "online",
            "mode": "production_cloudflare_bypass",
            "cached_players": data_manager.get_cached_players_count(),
            "detective_targets": len(data_manager.detective_targets),
            "browser_ready": data_manager.browser is not None,
            "timestamp": datetime.utcnow().isoformat()
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
            .limit(200)
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

# --- BACKGROUND WORKERS ---
def list_scraper_worker():
    """Background worker for scraping player list"""
    while True:
        try:
            print(f"\n[LIST_WORKER] Starting player list scrape...")
            
            if not data_manager.init_browser():
                print("[LIST_WORKER] ❌ Failed to initialize browser")
                time.sleep(MAIN_LIST_INTERVAL)
                continue
            
            # Get player list data
            data = bypass_cloudflare_and_get_json(data_manager.browser, USER_LIST_URL)
            
            if data:
                # Handle wrapper format
                if isinstance(data, dict) and 'data' in data:
                    player_list = data['data']
                elif isinstance(data, list):
                    player_list = data
                else:
                    print("[LIST_WORKER] ❌ Unexpected data format")
                    time.sleep(MAIN_LIST_INTERVAL)
                    continue
                
                if isinstance(player_list, list) and len(player_list) > 0:
                    print(f"[LIST_WORKER] ✅ Retrieved {len(player_list)} players")
                    
                    cached_count = 0
                    for player in player_list:
                        if isinstance(player, dict):
                            username = (player.get('username') or player.get('uname') or 
                                      player.get('name') or player.get('player_name'))
                            user_id = (player.get('user_id') or player.get('id') or 
                                     player.get('player_id'))
                            
                            if username:
                                # Normalize data
                                normalized = {
                                    "id": str(user_id) if user_id else None,
                                    "user_id": str(user_id) if user_id else None,
                                    "uname": username,
                                    "username": username,
                                    "rank_name": player.get('rank_name') or player.get('rank'),
                                    "plating": player.get('plating'),
                                    "position": player.get('position'),
                                    "status": player.get('status'),
                                    "f_name": player.get('f_name') or (player.get('family', {}) or {}).get('name'),
                                }
                                
                                if data_manager.cache_player_data(username, normalized, user_id):
                                    cached_count += 1
                    
                    print(f"[LIST_WORKER] 💾 Cached {cached_count} players")
                else:
                    print("[LIST_WORKER] ❌ No valid player data")
            else:
                print("[LIST_WORKER] ❌ Failed to get player list")
                
        except Exception as e:
            print(f"[LIST_WORKER] ❌ Error: {e}")
        
        print(f"[LIST_WORKER] ⏳ Next update in {MAIN_LIST_INTERVAL} seconds")
        time.sleep(MAIN_LIST_INTERVAL)

def detail_scraper_worker():
    """Background worker for scraping detective target details"""
    while True:
        try:
            if not data_manager.detective_targets:
                print(f"[DETAIL_WORKER] ℹ️ No detective targets configured")
                time.sleep(DETAIL_BATCH_INTERVAL)
                continue
            
            print(f"\n[DETAIL_WORKER] Processing {len(data_manager.detective_targets)} detective targets...")
            
            if not data_manager.init_browser():
                print("[DETAIL_WORKER] ❌ Failed to initialize browser")
                time.sleep(DETAIL_BATCH_INTERVAL)
                continue
            
            for username in list(data_manager.detective_targets):
                try:
                    url = USER_DETAIL_URL_TEMPLATE.format(username)
                    print(f"[DETAIL_WORKER] Getting {username}...")
                    
                    data = bypass_cloudflare_and_get_json(data_manager.browser, url, timeout=30)
                    
                    if data:
                        # Handle wrapper if present
                        if isinstance(data, dict) and 'data' in data:
                            detail_data = data['data']
                        else:
                            detail_data = data
                        
                        if isinstance(detail_data, dict):
                            # Cache the detailed data
                            user_id = detail_data.get('user_id') or detail_data.get('id')
                            if data_manager.cache_player_data(username, detail_data, user_id):
                                print(f"[DETAIL_WORKER] ✅ Updated {username}")
                                data_manager.notify_backend_update({"username": username})
                        else:
                            print(f"[DETAIL_WORKER] ⚠️ Invalid data format for {username}")
                    else:
                        print(f"[DETAIL_WORKER] ❌ Failed to get data for {username}")
                    
                    # Random delay to avoid detection
                    delay = random.uniform(3, 7)
                    time.sleep(delay)
                    
                except Exception as e:
                    print(f"[DETAIL_WORKER] ❌ Error processing {username}: {e}")
                
        except Exception as e:
            print(f"[DETAIL_WORKER] ❌ Worker error: {e}")
            
        print(f"[DETAIL_WORKER] ⏳ Next batch in {DETAIL_BATCH_INTERVAL} seconds")
        time.sleep(DETAIL_BATCH_INTERVAL)

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    try:
        print("\n" + "="*60)
        print("🎯 OMERTA INTELLIGENCE SCRAPING SERVICE - PRODUCTION")
        print("🛡️  ADVANCED CLOUDFLARE BYPASS ENABLED")
        print("🔧 USERNAME-FIRST ARCHITECTURE")
        print("="*60)
        
        # Start Flask API
        flask_thread = threading.Thread(
            target=lambda: app.run(debug=False, use_reloader=False, port=5001, host='127.0.0.1')
        )
        flask_thread.daemon = True
        flask_thread.start()
        print("[WEB] Flask API started on http://127.0.0.1:5001")

        # Start background workers
        list_thread = threading.Thread(target=list_scraper_worker)
        list_thread.daemon = True
        list_thread.start()
        print("[WORKER] List scraper started")

        detail_thread = threading.Thread(target=detail_scraper_worker)
        detail_thread.daemon = True
        detail_thread.start()
        print("[WORKER] Detail scraper started")

        print(f"\n✅ All services active!")
        print(f"📊 API Status: http://127.0.0.1:5001/api/scraping/status")
        print(f"🎯 Detective Targets: {len(data_manager.detective_targets)}")
        print(f"💾 Cached Players: {data_manager.get_cached_players_count()}")
        
        # Keep main thread alive
        while True:
            time.sleep(100)

    except KeyboardInterrupt:
        print("\n👋 Scraping service stopped by user.")
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
    finally:
        if data_manager.browser:
            try:
                data_manager.browser.quit()
                print("[CLEANUP] Browser closed.")
            except:
                pass