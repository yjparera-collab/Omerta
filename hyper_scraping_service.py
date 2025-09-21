import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import threading
from flask import Flask, request, jsonify
from queue import Queue, PriorityQueue
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3
import hashlib
import os
import requests
import asyncio
from threading import Lock

# --- HYPER-PERFORMANCE CONFIGURATION ---
USER_LIST_URL = "https://barafranca.com/index.php?module=API&action=users"
USER_DETAIL_URL_TEMPLATE = "https://barafranca.com/index.php?module=API&action=user&name={}"

# PERFORMANCE SETTINGS - AGGRESSIVE MODE
LIST_SCAN_INTERVAL = 30  # Still scan list every 30s
MAX_BROWSER_INSTANCES = 4  # Multiple browser instances
MAX_TABS_PER_BROWSER = 10  # 10 tabs per browser = 40 total
HYPER_BATCH_SIZE = 40  # Process 40 players at once
AGGRESSIVE_CACHE_DURATION = 15  # Very short cache for real-time data
ULTRA_PRIORITY_CACHE = 5  # 5 seconds for high priority targets

# WEALTH LEVEL MAPPING
WEALTH_LEVELS = {
    0: "Straydog",
    1: "Poor", 
    2: "Nouveau Riche",
    3: "Rich",
    4: "Very Rich", 
    5: "Too Rich to be True",
    6: "Richer than God"
}

# PLATING LEVEL MAPPING  
PLATING_LEVELS = {
    "Very High": {"level": 5, "color": "emerald", "vulnerability": "Minimal"},
    "High": {"level": 4, "color": "green", "vulnerability": "Low"},
    "Medium": {"level": 3, "color": "yellow", "vulnerability": "Moderate"}, 
    "Low": {"level": 2, "color": "orange", "vulnerability": "High"},
    "Very Low": {"level": 1, "color": "red", "vulnerability": "Critical"},
    "None": {"level": 0, "color": "red", "vulnerability": "EXPOSED"}
}

class HyperIntelligenceManager:
    def __init__(self):
        self.db = self.init_database()
        self.full_user_list = []
        self.target_families = []
        self.detective_targets = set()
        self.tracked_players = set()  # NEW: Explicitly tracked players
        self.detailed_user_info = {}
        self.last_list_update = None
        self.lock = Lock()
        self.previous_player_data = {}
        self.notification_callbacks = []
        
        # PERFORMANCE TRACKING
        self.scraping_stats = {
            "total_scraped": 0,
            "scrapes_per_minute": 0,
            "last_performance_check": time.time(),
            "browser_instances": 0,
            "active_tabs": 0
        }
        
        self.load_tracked_players()

    def init_database(self):
        conn = sqlite3.connect('omerta_hyper_intelligence.db', check_same_thread=False)
        
        # Enhanced tables for hyper-performance tracking
        conn.execute('''
            CREATE TABLE IF NOT EXISTS player_cache (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                data TEXT,
                last_updated TIMESTAMP,
                priority INTEGER DEFAULT 1,
                scrape_count INTEGER DEFAULT 0,
                wealth_level INTEGER DEFAULT 0,
                plating_level TEXT DEFAULT 'Unknown',
                is_tracked INTEGER DEFAULT 0
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS hyper_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT,
                username TEXT,
                event_type TEXT,
                old_value TEXT,
                new_value TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                family TEXT,
                wealth_change INTEGER DEFAULT 0,
                plating_change TEXT
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS tracked_players (
                player_id TEXT PRIMARY KEY,
                username TEXT,
                added_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                priority_level INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS scraping_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                players_scraped INTEGER,
                time_taken REAL,
                scrapes_per_second REAL,
                browser_instances INTEGER,
                active_tabs INTEGER
            )
        ''')

        conn.commit()
        return conn

    def add_tracked_player(self, player_id, username, priority=1):
        """Add player to high-priority tracking"""
        with self.lock:
            self.tracked_players.add(player_id)
            self.db.execute(
                'INSERT OR REPLACE INTO tracked_players (player_id, username, priority_level, is_active) VALUES (?, ?, ?, 1)',
                (player_id, username, priority)
            )
            # Mark in player_cache as tracked
            self.db.execute(
                'UPDATE player_cache SET is_tracked = 1 WHERE user_id = ?',
                (player_id,)
            )
            self.db.commit()

    def load_tracked_players(self):
        """Load all tracked players"""
        cursor = self.db.execute('SELECT player_id FROM tracked_players WHERE is_active = 1')
        for row in cursor.fetchall():
            self.tracked_players.add(row[0])

    def get_tracked_players_list(self):
        """Get list of tracked players with their data"""
        cursor = self.db.execute('''
            SELECT tp.player_id, tp.username, tp.priority_level, pc.data, pc.wealth_level, pc.plating_level
            FROM tracked_players tp
            LEFT JOIN player_cache pc ON tp.player_id = pc.user_id
            WHERE tp.is_active = 1
            ORDER BY tp.priority_level ASC
        ''')
        
        tracked = []
        for row in cursor.fetchall():
            player_id, username, priority, data, wealth, plating = row
            player_data = json.loads(data) if data else {}
            tracked.append({
                'player_id': player_id,
                'username': username,
                'priority': priority,
                'wealth_level': wealth,
                'wealth_text': WEALTH_LEVELS.get(wealth, 'Unknown'),
                'plating': plating,
                'plating_info': PLATING_LEVELS.get(plating, {'level': 0, 'color': 'gray', 'vulnerability': 'Unknown'}),
                'kills': player_data.get('kills', 0),
                'shots': player_data.get('bullets_shot', {}).get('total', 0)
            })
        
        return tracked

    def cache_player_data_enhanced(self, user_id, username, data, priority=1):
        """Enhanced caching with wealth/plating tracking"""
        # Process wealth level
        wealth_num = data.get('wealth', 0)
        wealth_text = WEALTH_LEVELS.get(wealth_num, 'Unknown')
        
        # Process plating
        plating = data.get('plating', 'Unknown')
        
        # Check for changes and log analytics
        self.log_enhanced_player_changes(user_id, username, data, wealth_num, plating)

        # Update cache with enhanced data
        is_tracked = 1 if user_id in self.tracked_players else 0
        
        self.db.execute('''
            INSERT OR REPLACE INTO player_cache 
            (user_id, username, data, last_updated, priority, wealth_level, plating_level, is_tracked, scrape_count) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT scrape_count FROM player_cache WHERE user_id = ?), 0) + 1)
        ''', (user_id, username, json.dumps(data), datetime.now().isoformat(), priority, wealth_num, plating, is_tracked, user_id))
        
        self.db.commit()
        self.detailed_user_info[user_id] = data
        
        # Update performance stats
        self.scraping_stats["total_scraped"] += 1

    def log_enhanced_player_changes(self, user_id, username, new_data, wealth_num, plating):
        """Enhanced change detection with wealth/plating tracking"""
        if user_id not in self.previous_player_data:
            self.previous_player_data[user_id] = {}
            return

        old_data = self.previous_player_data[user_id]
        family_name = new_data.get('family', {}).get('name', 'Independent')

        # Track wealth changes
        old_wealth = old_data.get('wealth', 0)
        if old_wealth != wealth_num:
            wealth_change = wealth_num - old_wealth
            self.db.execute('''
                INSERT INTO hyper_analytics 
                (player_id, username, event_type, old_value, new_value, family, wealth_change) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, 'wealth_change', str(old_wealth), str(wealth_num), family_name, wealth_change))
            
            # Generate wealth change notification
            old_wealth_text = WEALTH_LEVELS.get(old_wealth, 'Unknown')
            new_wealth_text = WEALTH_LEVELS.get(wealth_num, 'Unknown')
            direction = "📈 INCREASED" if wealth_change > 0 else "📉 DECREASED"
            
            message = f"{direction}: {username} ({family_name}) wealth changed from {old_wealth_text} to {new_wealth_text}"
            self.create_intelligence_notification(user_id, username, 'wealth_change', message, {
                'old_wealth': old_wealth_text,
                'new_wealth': new_wealth_text,
                'family': family_name,
                'change': wealth_change
            })

        # Track plating changes - CRITICAL INTELLIGENCE  
        old_plating = old_data.get('plating', 'Unknown')
        if old_plating != plating:
            self.db.execute('''
                INSERT INTO hyper_analytics 
                (player_id, username, event_type, old_value, new_value, family, plating_change) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, 'plating_change', old_plating, plating, family_name, plating))
            
            # CRITICAL: Plating vulnerability alerts
            old_info = PLATING_LEVELS.get(old_plating, {'level': 0, 'vulnerability': 'Unknown'})
            new_info = PLATING_LEVELS.get(plating, {'level': 0, 'vulnerability': 'Unknown'})
            
            if new_info['level'] < old_info['level']:
                # CRITICAL: Plating decreased - target is more vulnerable
                message = f"🚨 VULNERABILITY ALERT: {username} ({family_name}) plating dropped from {old_plating} to {plating} - {new_info['vulnerability']} RISK!"
                self.create_intelligence_notification(user_id, username, 'plating_vulnerability', message, {
                    'old_plating': old_plating,
                    'new_plating': plating,
                    'vulnerability_level': new_info['vulnerability'],
                    'family': family_name,
                    'criticality': 'HIGH' if new_info['level'] <= 1 else 'MEDIUM'
                })

        # Standard kill/shot tracking (enhanced)
        old_kills = old_data.get('kills', 0)
        new_kills = new_data.get('kills', 0)
        if old_kills != new_kills and isinstance(new_kills, int):
            kill_diff = new_kills - old_kills
            if kill_diff > 0:
                message = f"🎯 ELIMINATION: {username} ({family_name}) scored {kill_diff} kill{'s' if kill_diff > 1 else ''} (Total: {new_kills})"
                self.create_intelligence_notification(user_id, username, 'kill_update', message, {
                    'kills_gained': kill_diff,
                    'total_kills': new_kills,
                    'family': family_name
                })

        # Track shots with enhanced details
        old_shots = old_data.get('bullets_shot', {}).get('total', 0)
        new_shots = new_data.get('bullets_shot', {}).get('total', 0)
        if old_shots != new_shots and isinstance(new_shots, int):
            shot_diff = new_shots - old_shots
            if shot_diff > 0:
                message = f"🔫 COMBAT ACTIVITY: {username} ({family_name}) fired {shot_diff} shot{'s' if shot_diff > 1 else ''} (Total: {new_shots})"
                self.create_intelligence_notification(user_id, username, 'shot_update', message, {
                    'shots_fired': shot_diff,
                    'total_shots': new_shots,
                    'family': family_name
                })

        self.db.commit()
        self.previous_player_data[user_id] = new_data.copy()

    def create_intelligence_notification(self, player_id, username, notification_type, message, data=None):
        """Create enhanced intelligence notification"""
        self.db.execute('''
            INSERT INTO intelligence_notifications 
            (player_id, username, notification_type, message, data) 
            VALUES (?, ?, ?, ?, ?)
        ''', (player_id, username, notification_type, message, json.dumps(data) if data else None))
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

    def notify_intelligence_update(self, notification_data):
        """Send notifications to callbacks"""
        for callback in self.notification_callbacks:
            try:
                callback(notification_data)
            except Exception as e:
                print(f"Error in notification callback: {e}")

    def add_notification_callback(self, callback):
        """Register callback for real-time notifications"""
        self.notification_callbacks.append(callback)

    def get_hyper_priority_targets(self):
        """Get players that need immediate scraping"""
        priority_targets = []
        
        # 1. Tracked players (highest priority)
        tracked_players = [u for u in self.full_user_list if u.get('id') in self.tracked_players]
        for player in tracked_players:
            priority_targets.append((0, player))  # Priority 0 = highest
            
        # 2. Family members (medium priority)
        if self.target_families:
            family_players = [u for u in self.full_user_list if u.get('f_name') in self.target_families and u.get('id') not in self.tracked_players]
            for player in family_players:
                priority_targets.append((1, player))  # Priority 1 = medium
                
        # 3. Recently active players (based on position changes)
        active_players = [u for u in self.full_user_list if u.get('position') > 0 and u.get('position') <= 50 and u.get('id') not in self.tracked_players]
        for player in active_players[:20]:  # Top 20 ranked players
            priority_targets.append((2, player))  # Priority 2 = low
        
        # Sort by priority and return
        priority_targets.sort(key=lambda x: x[0])
        return priority_targets

    def get_scraping_performance(self):
        """Get scraping performance metrics"""
        current_time = time.time()
        time_since_last_check = current_time - self.scraping_stats["last_performance_check"]
        
        if time_since_last_check >= 60:  # Calculate per minute
            scrapes_per_minute = self.scraping_stats["total_scraped"] / (time_since_last_check / 60)
            self.scraping_stats["scrapes_per_minute"] = scrapes_per_minute
            self.scraping_stats["last_performance_check"] = current_time
            
            # Log performance to database
            self.db.execute('''
                INSERT INTO scraping_performance 
                (players_scraped, time_taken, scrapes_per_second, browser_instances, active_tabs)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                self.scraping_stats["total_scraped"],
                time_since_last_check,
                scrapes_per_minute / 60,
                self.scraping_stats["browser_instances"], 
                self.scraping_stats["active_tabs"]
            ))
            self.db.commit()
        
        return self.scraping_stats

# HYPER-PERFORMANCE SCRAPING ENGINE
class HyperScrapingEngine:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.browser_pool = []
        self.setup_browser_pool()
        
    def setup_browser_pool(self):
        """Setup multiple browser instances for maximum throughput"""
        for i in range(MAX_BROWSER_INSTANCES):
            try:
                options = uc.ChromeOptions()
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-extensions')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-images')  # Skip images for speed
                options.add_argument('--disable-javascript')  # Skip JS for speed (API doesn't need it)
                
                driver = uc.Chrome(options=options)
                self.browser_pool.append(driver)
                print(f"[HYPER] Browser instance {i+1} initialized")
                
                # Initial Cloudflare setup
                self.setup_browser_session(driver, f"Browser-{i+1}")
                
            except Exception as e:
                print(f"[ERROR] Failed to initialize browser {i+1}: {e}")
        
        self.data_manager.scraping_stats["browser_instances"] = len(self.browser_pool)
        print(f"[HYPER] Initialized {len(self.browser_pool)} browser instances")

    def setup_browser_session(self, driver, worker_name):
        """Setup Cloudflare bypass for browser"""
        try:
            print(f"[{worker_name}] Setting up Cloudflare bypass...")
            driver.get(USER_LIST_URL)
            time.sleep(8)
            
            if "Verifieer dat u een mens bent" in driver.page_source or "Verify you are human" in driver.page_source:
                print(f"[{worker_name}] Manual CAPTCHA required")
                input(f"Solve CAPTCHA for {worker_name} and press ENTER...")
            else:
                print(f"[{worker_name}] Cloudflare automatically passed!")
                
            time.sleep(2)
            return True
        except Exception as e:
            print(f"[ERROR] {worker_name} setup failed: {e}")
            return False

    def hyper_scrape_batch(self, priority_targets):
        """Scrape multiple players simultaneously using all browsers"""
        if not priority_targets:
            return
            
        print(f"[HYPER] Processing {len(priority_targets)} targets across {len(self.browser_pool)} browsers")
        
        # Distribute targets across browsers
        browser_tasks = [[] for _ in range(len(self.browser_pool))]
        for i, (priority, player) in enumerate(priority_targets):
            browser_index = i % len(self.browser_pool)
            browser_tasks[browser_index].append((priority, player))
        
        # Execute scraping across all browsers simultaneously
        with ThreadPoolExecutor(max_workers=len(self.browser_pool)) as executor:
            futures = []
            for i, tasks in enumerate(browser_tasks):
                if tasks:
                    future = executor.submit(self.scrape_browser_batch, self.browser_pool[i], tasks, f"Browser-{i+1}")
                    futures.append(future)
            
            # Wait for all browsers to complete
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    completed += result
                except Exception as e:
                    print(f"[ERROR] Browser batch failed: {e}")
        
        print(f"[HYPER] Completed scraping {completed} players")

    def scrape_browser_batch(self, driver, tasks, browser_name):
        """Scrape batch of players in single browser using multiple tabs"""
        completed = 0
        
        for priority, player in tasks:
            try:
                username = player.get('uname')
                if not username:
                    continue
                    
                # Check cache first (very short cache for tracked players)
                cache_duration = ULTRA_PRIORITY_CACHE if player.get('id') in self.data_manager.tracked_players else AGGRESSIVE_CACHE_DURATION
                cached_data = self.get_cached_data_if_fresh(player.get('id'), cache_duration)
                
                if cached_data:
                    continue  # Skip if recently cached
                
                # Scrape player data
                detail_url = USER_DETAIL_URL_TEMPLATE.format(username)
                driver.get(detail_url)
                time.sleep(0.5)  # Very short wait for performance
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                response_data = json.loads(soup.find('body').get_text())
                
                if 'data' in response_data:
                    player_details = response_data['data']
                    priority_level = 0 if player.get('id') in self.data_manager.tracked_players else 1
                    
                    # Cache with enhanced data processing
                    self.data_manager.cache_player_data_enhanced(
                        player['id'], username, player_details, priority_level
                    )
                    completed += 1
                    
                    if completed % 10 == 0:
                        print(f"[{browser_name}] Processed {completed} players...")
                        
            except Exception as e:
                print(f"[ERROR] {browser_name} failed to process {username}: {e}")
                continue
        
        return completed

    def get_cached_data_if_fresh(self, user_id, max_age_seconds):
        """Check if we have fresh cached data"""
        try:
            cursor = self.data_manager.db.execute(
                'SELECT last_updated FROM player_cache WHERE user_id = ?', (user_id,)
            )
            result = cursor.fetchone()
            if result:
                last_updated = datetime.fromisoformat(result[0])
                if datetime.now() - last_updated < timedelta(seconds=max_age_seconds):
                    return True
        except:
            pass
        return False

# Initialize the hyper system
data_manager = HyperIntelligenceManager()
scraping_engine = HyperScrapingEngine(data_manager)

# ENHANCED FLASK API
app = Flask(__name__)

@app.route('/api/hyper/status')
def get_hyper_status():
    """Get hyper scraping status"""
    performance = data_manager.get_scraping_performance()
    
    cursor = data_manager.db.execute('SELECT COUNT(*) FROM player_cache WHERE is_tracked = 1')
    tracked_count = cursor.fetchone()[0]
    
    return jsonify({
        "status": "HYPER_ACTIVE",
        "performance": performance,
        "tracked_players": tracked_count,
        "browser_instances": len(scraping_engine.browser_pool),
        "max_concurrent_scrapes": MAX_BROWSER_INSTANCES * MAX_TABS_PER_BROWSER,
        "cache_settings": {
            "tracked_players_cache": f"{ULTRA_PRIORITY_CACHE}s",
            "regular_cache": f"{AGGRESSIVE_CACHE_DURATION}s"
        }
    })

@app.route('/api/hyper/tracked-players')
def get_tracked_players():
    """Get all tracked players with enhanced data"""
    tracked = data_manager.get_tracked_players_list()
    return jsonify({"tracked_players": tracked})

@app.route('/api/hyper/add-tracked', methods=['POST'])
def add_tracked_player():
    """Add player to high-priority tracking"""
    try:
        data = request.json
        username = data.get('username')
        priority = data.get('priority', 1)
        
        # Find player ID from username
        player = next((p for p in data_manager.full_user_list if p.get('uname') == username), None)
        if not player:
            return jsonify({"error": "Player not found"}), 404
            
        data_manager.add_tracked_player(player['id'], username, priority)
        
        return jsonify({
            "message": f"Added {username} to high-priority tracking",
            "priority": priority
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# HYPER SCRAPING MAIN LOOP
def hyper_scraping_loop():
    """Main hyper-performance scraping loop"""
    while True:
        try:
            start_time = time.time()
            
            # Get high-priority targets
            priority_targets = data_manager.get_hyper_priority_targets()
            
            if priority_targets:
                # Execute hyper-scraping
                scraping_engine.hyper_scrape_batch(priority_targets[:HYPER_BATCH_SIZE])
                
                # Performance logging  
                elapsed = time.time() - start_time
                scrapes_per_second = len(priority_targets) / elapsed if elapsed > 0 else 0
                
                print(f"[HYPER] Scraped {len(priority_targets)} players in {elapsed:.2f}s ({scrapes_per_second:.1f} players/sec)")
            
            # Short sleep before next batch
            time.sleep(5)  # Very aggressive - scrape every 5 seconds
            
        except Exception as e:
            print(f"[ERROR] Hyper scraping loop failed: {e}")
            time.sleep(10)

if __name__ == "__main__":
    print("\n🚀 STARTING HYPER-PERFORMANCE OMERTA INTELLIGENCE ENGINE")
    print("=" * 80)
    print(f"⚡ Max Browser Instances: {MAX_BROWSER_INSTANCES}")
    print(f"⚡ Max Tabs per Browser: {MAX_TABS_PER_BROWSER}")  
    print(f"⚡ Total Concurrent Scrapes: {MAX_BROWSER_INSTANCES * MAX_TABS_PER_BROWSER}")
    print(f"⚡ Hyper Batch Size: {HYPER_BATCH_SIZE}")
    print(f"⚡ Aggressive Cache: {AGGRESSIVE_CACHE_DURATION}s")
    print(f"⚡ Ultra Priority Cache: {ULTRA_PRIORITY_CACHE}s")
    print("=" * 80)
    
    # Start Flask API
    flask_thread = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False, port=5001, host='127.0.0.1'))
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start hyper scraping loop
    scraping_thread = threading.Thread(target=hyper_scraping_loop)
    scraping_thread.daemon = True
    scraping_thread.start()
    
    print("🎯 HYPER INTELLIGENCE ENGINE ACTIVE!")
    print("📊 Performance tracking: http://localhost:5001/api/hyper/status")
    
    try:
        while True:
            time.sleep(30)
            performance = data_manager.get_scraping_performance()
            print(f"[STATS] Scraped: {performance['total_scraped']} | Rate: {performance['scrapes_per_minute']:.1f}/min")
    except KeyboardInterrupt:
        print("\n🛑 Shutting down hyper engine...")
        for driver in scraping_engine.browser_pool:
            driver.quit()