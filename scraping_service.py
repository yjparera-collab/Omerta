import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import threading
from flask import Flask, request, jsonify
from queue import Queue, PriorityQueue
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import hashlib
import os
import requests

# --- CONFIGURATIE ---
USER_LIST_URL = "https://barafranca.com/index.php?module=API&action=users"
USER_DETAIL_URL_TEMPLATE = "https://barafranca.com/index.php?module=API&action=user&name={}"
MAIN_LIST_INTERVAL = 30
MAX_CONCURRENT_TABS = 2
CACHE_DURATION = 30  # 30 seconden cache voor detective targets
BATCH_SIZE = 5

# --- DATABASE SETUP ---
def init_database():
    conn = sqlite3.connect('omerta_intelligence.db', check_same_thread=False)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS player_cache (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            data TEXT,
            last_updated TIMESTAMP,
            priority INTEGER DEFAULT 1
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS analytics_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT,
            username TEXT,
            event_type TEXT,
            old_value TEXT,
            new_value TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            family TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS detective_targets (
            player_id TEXT PRIMARY KEY,
            username TEXT,
            added_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS intelligence_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT,
            username TEXT,
            notification_type TEXT,
            message TEXT,
            data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    return conn

# --- SMART DATA MANAGER ---
class IntelligenceDataManager:
    def __init__(self):
        self.db = init_database()
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
        cursor = self.db.execute('SELECT player_id FROM detective_targets WHERE is_active = 1')
        for row in cursor.fetchall():
            self.detective_targets.add(row[0])

    def add_detective_targets(self, usernames):
        added_count = 0
        with self.lock:
            for user in self.full_user_list:
                if user.get('uname') in usernames:
                    player_id = user['id']
                    if player_id not in self.detective_targets:
                        self.detective_targets.add(player_id)
                        self.db.execute(
                            'INSERT OR REPLACE INTO detective_targets (player_id, username, is_active) VALUES (?, ?, 1)',
                            (player_id, user.get('uname'))
                        )
                        added_count += 1
            self.db.commit()
        return added_count

    def remove_detective_target(self, player_id):
        with self.lock:
            if player_id in self.detective_targets:
                self.detective_targets.remove(player_id)
                self.db.execute('UPDATE detective_targets SET is_active = 0 WHERE player_id = ?', (player_id,))
                self.db.commit()
                return True
        return False

    def get_detective_targets_list(self):
        cursor = self.db.execute('SELECT player_id, username FROM detective_targets WHERE is_active = 1')
        return [{'player_id': row[0], 'username': row[1]} for row in cursor.fetchall()]

    def get_cached_player_data(self, user_id):
        cursor = self.db.execute(
            'SELECT data, last_updated FROM player_cache WHERE user_id = ?',
            (user_id,)
        )
        result = cursor.fetchone()
        if result:
            data, last_updated = result
            cache_duration = CACHE_DURATION if user_id in self.detective_targets else 300
            if datetime.now() - datetime.fromisoformat(last_updated) < timedelta(seconds=cache_duration):
                return json.loads(data)
        return None

    def cache_player_data(self, user_id, username, data, priority=1):
        # Check for changes and log analytics
        self.log_player_changes(user_id, username, data)

        self.db.execute(
            'INSERT OR REPLACE INTO player_cache (user_id, username, data, last_updated, priority) VALUES (?, ?, ?, ?, ?)',
            (user_id, username, json.dumps(data), datetime.now().isoformat(), priority)
        )
        self.db.commit()

        self.detailed_user_info[user_id] = data

    def create_intelligence_notification(self, player_id, username, notification_type, message, data=None):
        """Create and store intelligence notification"""
        self.db.execute(
            'INSERT INTO intelligence_notifications (player_id, username, notification_type, message, data) VALUES (?, ?, ?, ?, ?)',
            (player_id, username, notification_type, message, json.dumps(data) if data else None)
        )
        self.db.commit()

        # Send real-time notification
        notification_data = {
            'type': notification_type,
            'player_id': player_id,
            'username': username,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self.notify_intelligence_update(notification_data)

    def log_player_changes(self, user_id, username, new_data):
        """Log significant changes and generate intelligence notifications"""
        if user_id not in self.previous_player_data:
            self.previous_player_data[user_id] = {}
            return

        old_data = self.previous_player_data[user_id]
        # Fix: Get family name properly from nested structure
        family_info = new_data.get('family', {})
        if isinstance(family_info, dict):
            family_name = family_info.get('name', 'Independent')
        else:
            family_name = 'Independent'

        # Check for kills change
        old_kills = old_data.get('kills', 0)
        new_kills = new_data.get('kills', 0)
        if old_kills != new_kills and isinstance(old_kills, int) and isinstance(new_kills, int):
            kill_diff = new_kills - old_kills
            if kill_diff > 0:
                self.db.execute(
                    'INSERT INTO analytics_log (player_id, username, event_type, old_value, new_value, family) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, username, 'kill', str(old_kills), str(new_kills), family_name)
                )
                
                # Generate intelligence notification
                message = f"[TARGET] {username} ({family_name}) scored {kill_diff} new kill{'s' if kill_diff > 1 else ''}"
                self.create_intelligence_notification(user_id, username, 'kill_update', message, {
                    'old_kills': old_kills,
                    'new_kills': new_kills,
                    'family': family_name
                })

        # Check for shots change
        old_shots = old_data.get('bullets_shot', {}).get('total', 0) if old_data.get('bullets_shot') else 0
        new_shots = new_data.get('bullets_shot', {}).get('total', 0) if new_data.get('bullets_shot') else 0
        if old_shots != new_shots and isinstance(old_shots, int) and isinstance(new_shots, int):
            shot_diff = new_shots - old_shots
            if shot_diff > 0:
                self.db.execute(
                    'INSERT INTO analytics_log (player_id, username, event_type, old_value, new_value, family) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, username, 'shot', str(old_shots), str(new_shots), family_name)
                )
                
                # Generate intelligence notification
                message = f"[SHOTS] {username} ({family_name}) fired {shot_diff} shot{'s' if shot_diff > 1 else ''}"
                self.create_intelligence_notification(user_id, username, 'shot_update', message, {
                    'old_shots': old_shots,
                    'new_shots': new_shots,
                    'family': family_name
                })

        # Check for plating change - CRITICAL INTELLIGENCE
        old_plating = old_data.get('plating', 'Unknown')
        new_plating = new_data.get('plating', 'Unknown')
        if old_plating != new_plating:
            if 'none' in new_plating.lower() or 'no plating' in new_plating.lower():
                self.db.execute(
                    'INSERT INTO analytics_log (player_id, username, event_type, old_value, new_value, family) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, username, 'plating', str(old_plating), str(new_plating), family_name)
                )
                
                # CRITICAL INTELLIGENCE NOTIFICATION
                message = f"[CRITICAL] CRITICAL: {username} ({family_name}) plating dropped to {new_plating} - VULNERABLE TARGET!"
                self.create_intelligence_notification(user_id, username, 'plating_drop', message, {
                    'old_plating': old_plating,
                    'new_plating': new_plating,
                    'family': family_name
                })

        # Check for profile visibility change
        old_kills_visible = old_data.get('kills') not in ['N/A', None, '']
        new_kills_visible = new_data.get('kills') not in ['N/A', None, '']
        if not old_kills_visible and new_kills_visible:
            message = f"[INTEL] {username} ({family_name}) profile became public - intelligence now available"
            self.create_intelligence_notification(user_id, username, 'profile_public', message, {
                'family': family_name,
                'kills': new_data.get('kills'),
                'shots': new_data.get('bullets_shot', {}).get('total', 0) if new_data.get('bullets_shot') else 0
            })

        self.db.commit()
        self.previous_player_data[user_id] = new_data.copy()

    def get_priority_players(self, limit=BATCH_SIZE):
        """Haal spelers op die het meest urgent een update nodig hebben"""
        all_targets = []

        # Add family-based targets
        if self.target_families:
            family_targets = [u for u in self.full_user_list if u.get('f_name') in self.target_families]
            all_targets.extend(family_targets)

        # Add individual detective targets
        detective_targets = [u for u in self.full_user_list if u.get('id') in self.detective_targets]
        all_targets.extend(detective_targets)

        # Remove duplicates
        seen_ids = set()
        unique_targets = []
        for player in all_targets:
            if player['id'] not in seen_ids:
                unique_targets.append(player)
                seen_ids.add(player['id'])

        # Check which ones need updates most urgently
        priority_players = []
        for player in unique_targets:
            cached_data = self.get_cached_player_data(player['id'])
            if not cached_data:
                priority_players.append((0, player))  # Highest priority for uncached
            else:
                # Higher priority for detective targets
                priority = 0 if player['id'] in self.detective_targets else 1
                priority_players.append((priority, player))

        # Sort by priority and return limited number
        priority_players.sort(key=lambda x: x[0])
        return priority_players[:limit]

    def get_recent_notifications(self, limit=50):
        """Get recent intelligence notifications"""
        cursor = self.db.execute('''
            SELECT username, notification_type, message, timestamp, data
            FROM intelligence_notifications
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        notifications = []
        for row in cursor.fetchall():
            username, notification_type, message, timestamp, data = row
            notifications.append({
                'username': username,
                'type': notification_type,
                'message': message,
                'timestamp': timestamp,
                'data': json.loads(data) if data else None
            })
        return notifications

# --- CLOUDFLARE SETUP ---
def setup_browser_session(driver, url, worker_name):
    print(f"[{worker_name}] Loading page: {url}")
    driver.get(url)
    print(f"[{worker_name}] Waiting 8 seconds...")
    time.sleep(8)
    if "Verifieer dat u een mens bent" in driver.page_source or "Verify you are human" in driver.page_source:
        input(f"\n!!! [ACTION REQUIRED for {worker_name}] Solve CAPTCHA and press ENTER !!!")
    else:
        print(f"[{worker_name}] Cloudflare automatically passed!")
    time.sleep(3)
    return True

# --- WORKER THREADS ---
def smart_list_worker(driver, data_manager, priority_queue):
    """Enhanced analyst worker - detects changes and triggers actions"""
    last_hash = None

    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ANALYST: Checking for changes...")
            driver.get(USER_LIST_URL)
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            user_list = json.loads(soup.find('body').get_text()).get('users', [])

            # Check for actual changes
            current_hash = hashlib.md5(json.dumps(user_list, sort_keys=True).encode()).hexdigest()

            if current_hash != last_hash:
                print(f"[ANALYST] Changes detected! Updating data...")
                with data_manager.lock:
                    data_manager.full_user_list = user_list
                    data_manager.last_list_update = datetime.now()

                # Add target players to priority queue
                priority_players = data_manager.get_priority_players()
                for priority, player in priority_players:
                    priority_queue.put((priority, player))

                last_hash = current_hash
                print(f"[ANALYST] {len(priority_players)} players added to processing queue")
                
                # Notify FastAPI about list update
                try:
                    requests.post('http://localhost:8001/api/internal/list-updated', 
                                json={'count': len(user_list), 'timestamp': datetime.now().isoformat()},
                                timeout=1)
                except:
                    pass  # FastAPI might not be running yet
            else:
                print(f"[ANALYST] No changes detected, skipping update")

        except Exception as e:
            print(f"[ERROR in Smart Analyst]: {e}")

        time.sleep(MAIN_LIST_INTERVAL)

def batch_detail_worker(driver, data_manager, priority_queue):
    """Process players in batches for efficiency"""
    while True:
        try:
            # Collect a batch of players
            batch = []
            for _ in range(BATCH_SIZE):
                if not priority_queue.empty():
                    priority, player = priority_queue.get()

                    # Check if this player still needs an update
                    cached_data = data_manager.get_cached_player_data(player['id'])
                    if not cached_data:  # Only if not recently cached
                        batch.append(player)

                    priority_queue.task_done()

            if not batch:
                time.sleep(5)  # Wait if there's no work
                continue

            print(f"[BATCH WORKER] Processing {len(batch)} players...")

            # Process the batch with optimized tab management
            for player in batch:
                process_player_optimized(driver, player, data_manager)
                time.sleep(1)  # Short pause between requests

        except Exception as e:
            print(f"[ERROR in Batch Worker]: {e}")
            time.sleep(10)

def process_player_optimized(driver, player, data_manager):
    """Optimized player processing with tab reuse"""
    try:
        username = player.get('uname')
        if not username:
            return

        print(f"  -> BATCH: Processing {username}...")

        # Reuse current tab instead of creating new tab
        detail_url = USER_DETAIL_URL_TEMPLATE.format(username)
        driver.get(detail_url)
        time.sleep(1.5)  # Reduced wait time

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        response_object = json.loads(soup.find('body').get_text())
        player_details = response_object.get('data', {})

        # Cache the complete player data
        data_manager.cache_player_data(player['id'], username, player_details)

        kills = player_details.get('kills', 'N/A')
        shots_obj = player_details.get('bullets_shot', {})
        total_shots = shots_obj.get('total', 'N/A') if shots_obj else 'N/A'

        print(f"  -> CACHED {username}: Kills={kills}, Shots={total_shots}")

    except Exception as e:
        print(f"[ERROR processing {username}]: {e}")

# --- GLOBALS ---
data_manager = IntelligenceDataManager()
setup_complete = threading.Event()
priority_queue = PriorityQueue()

# --- FLASK API ---
app = Flask(__name__)

@app.route('/api/scraping/status')
def get_status():
    """Get scraping service status"""
    cursor = data_manager.db.execute('SELECT COUNT(*) FROM player_cache')
    cached_players = cursor.fetchone()[0]

    return jsonify({
        "status": "active",
        "cached_players": cached_players,
        "target_families": len(data_manager.target_families),
        "detective_targets": len(data_manager.detective_targets),
        "queue_size": priority_queue.qsize(),
        "last_list_update": data_manager.last_list_update.isoformat() if data_manager.last_list_update else None
    })

@app.route('/api/scraping/players')
def get_players():
    """Get all cached players"""
    with data_manager.lock:
        return jsonify({
            "players": data_manager.full_user_list,
            "last_updated": data_manager.last_list_update.isoformat() if data_manager.last_list_update else None
        })

@app.route('/api/scraping/player/<player_id>')
def get_player_details(player_id):
    """Get detailed player information"""
    cached_data = data_manager.get_cached_player_data(player_id)
    if cached_data:
        return jsonify(cached_data)
    else:
        return jsonify({"error": "No cached data available"}), 404

@app.route('/api/scraping/notifications')
def get_notifications():
    """Get recent intelligence notifications"""
    notifications = data_manager.get_recent_notifications()
    return jsonify({"notifications": notifications})

@app.route('/api/scraping/detective/add', methods=['POST'])
def add_detective_targets():
    """Add players to detective tracking"""
    try:
        usernames = request.json.get('usernames', [])
        if not usernames:
            return jsonify({"error": "No usernames provided"}), 400

        added_count = data_manager.add_detective_targets(usernames)

        # Immediately add these players to the priority queue
        with data_manager.lock:
            for user in data_manager.full_user_list:
                if user.get('uname') in usernames:
                    priority_queue.put((0, user))  # Highest priority

        return jsonify({
            "message": f"Detective tracking started for {added_count} players",
            "tracked_players": usernames
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/families/set', methods=['POST'])
def set_target_families():
    """Set target families for tracking"""
    try:
        families = request.json.get('families', [])
        with data_manager.lock:
            data_manager.target_families = families
        
        # Trigger immediate scan of family members
        with data_manager.lock:
            for user in data_manager.full_user_list:
                if user.get('f_name') in families:
                    priority_queue.put((1, user))

        return jsonify({"message": f"Target families set: {', '.join(families)}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    driver = None
    try:
        print("\n[SETUP] Starting Omerta Intelligence Scraping Service...")
        
        # Start Flask API
        flask_thread = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False, port=5001, host='127.0.0.1'))
        flask_thread.daemon = True
        flask_thread.start()
        print("[WEB] Flask scraping API started on http://127.0.0.1:5001")

        # Setup optimized browser
        print("\n--- SETTING UP BROWSER FOR CLOUDFLARE ---")
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')

        driver = uc.Chrome(options=options)
        setup_browser_session(driver, USER_LIST_URL, "Intelligence Worker")

        # Signal setup complete
        setup_complete.set()

        # Start worker threads
        list_thread = threading.Thread(target=smart_list_worker, args=(driver, data_manager, priority_queue))
        list_thread.daemon = True
        list_thread.start()

        batch_thread = threading.Thread(target=batch_detail_worker, args=(driver, data_manager, priority_queue))
        batch_thread.daemon = True
        batch_thread.start()

        print(f"\n[START] OMERTA INTELLIGENCE SCRAPING ACTIVE")
        print(f"[LIVE] Smart List Worker: Every {MAIN_LIST_INTERVAL} seconds")
        print(f"[REFRESH] Batch Detail Worker: {BATCH_SIZE} players per batch")
        print(f"[CACHE] Detective Cache: {CACHE_DURATION}s cache duration")
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
        if hasattr(data_manager, 'db'):
            data_manager.db.close()
        print("[SECURE] Browser and database connections closed.")