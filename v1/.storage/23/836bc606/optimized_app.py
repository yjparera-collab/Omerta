import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import threading
from flask import Flask, render_template, request, jsonify, redirect, url_for
from queue import Queue, PriorityQueue
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import hashlib
import os

# --- CONFIGURATIE ---
USER_LIST_URL = "https://barafranca.com/index.php?module=API&action=users"
USER_DETAIL_URL_TEMPLATE = "https://barafranca.com/index.php?module=API&action=user&name={}"
MAIN_LIST_INTERVAL = 30
MAX_CONCURRENT_TABS = 2  # Verminderd voor efficiëntie
CACHE_DURATION = 300  # 5 minuten cache voor individuele spelers
BATCH_SIZE = 5  # Aantal spelers per batch

# --- DATABASE SETUP ---
def init_database():
    conn = sqlite3.connect('player_cache.db', check_same_thread=False)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS player_cache (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            data TEXT,
            last_updated TIMESTAMP,
            priority INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    return conn

# --- VERBETERDE DATA STRUCTUUR ---
class SmartDataManager:
    def __init__(self):
        self.db = init_database()
        self.full_user_list = []
        self.target_families = []
        self.detailed_user_info = {}
        self.last_list_update = None
        self.lock = threading.Lock()
        
    def get_cached_player_data(self, user_id):
        cursor = self.db.execute(
            'SELECT data, last_updated FROM player_cache WHERE user_id = ?', 
            (user_id,)
        )
        result = cursor.fetchone()
        if result:
            data, last_updated = result
            if datetime.now() - datetime.fromisoformat(last_updated) < timedelta(seconds=CACHE_DURATION):
                return json.loads(data)
        return None
    
    def cache_player_data(self, user_id, username, data, priority=1):
        self.db.execute(
            'INSERT OR REPLACE INTO player_cache (user_id, username, data, last_updated, priority) VALUES (?, ?, ?, ?, ?)',
            (user_id, username, json.dumps(data), datetime.now().isoformat(), priority)
        )
        self.db.commit()
        
        # Update ook de in-memory detailed_user_info voor backward compatibility
        self.detailed_user_info[user_id] = data
    
    def get_priority_players(self, limit=BATCH_SIZE):
        """Haal spelers op die het meest urgent een update nodig hebben"""
        if not self.target_families:
            return []
            
        # Get target family players from current user list
        target_players = [u for u in self.full_user_list if u.get('f_name') in self.target_families]
        
        # Check which ones need updates most urgently
        priority_players = []
        for player in target_players:
            cached_data = self.get_cached_player_data(player['id'])
            if not cached_data:
                priority_players.append((0, player))  # Highest priority for uncached
            else:
                # Lower priority for recently cached
                priority_players.append((1, player))
        
        # Sort by priority and return limited number
        priority_players.sort(key=lambda x: x[0])
        return priority_players[:limit]

# --- GLOBALE INSTANTIES ---
data_manager = SmartDataManager()
setup_complete = threading.Event()
priority_queue = PriorityQueue()

# --- VERBETERDE CLOUDFLARE SETUP ---
def setup_browser_session(driver, url, worker_name):
    print(f"[{worker_name}] Pagina laden: {url}")
    driver.get(url)
    print(f"[{worker_name}] Wachten voor 8 seconden...")
    time.sleep(8)
    if "Verifieer dat u een mens bent" in driver.page_source:
        input(f"\n!!! [ACTIE VEREIST voor {worker_name}] Los de CAPTCHA op en druk hier op ENTER !!!")
    else:
        print(f"[{worker_name}] Cloudflare automatisch gepasseerd!")
    time.sleep(3)
    return True

# --- GEOPTIMALISEERDE WORKERS ---
def smart_list_worker(driver):
    """Verbeterde analist die alleen bij wijzigingen actie onderneemt"""
    setup_complete.wait()
    last_hash = None
    
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] SMART ANALIST: Controleren op wijzigingen...")
            driver.get(USER_LIST_URL)
            time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            user_list = json.loads(soup.find('body').get_text()).get('users', [])
            
            # Check of er daadwerkelijk wijzigingen zijn
            current_hash = hashlib.md5(json.dumps(user_list, sort_keys=True).encode()).hexdigest()
            
            if current_hash != last_hash:
                print(f"[ANALIST] Wijzigingen gedetecteerd! Updating data...")
                with data_manager.lock:
                    data_manager.full_user_list = user_list
                    data_manager.last_list_update = datetime.now()
                    
                # Voeg alleen target family spelers toe aan priority queue
                priority_players = data_manager.get_priority_players()
                for priority, player in priority_players:
                    priority_queue.put((priority, player))
                
                last_hash = current_hash
                print(f"[ANALIST] {len(priority_players)} spelers toegevoegd aan verwerkingsqueue")
            else:
                print(f"[ANALIST] Geen wijzigingen gedetecteerd, sla update over")
                
        except Exception as e:
            print(f"[FOUT in Smart Analist]: {e}")
        
        time.sleep(MAIN_LIST_INTERVAL)

def batch_detail_worker(driver):
    """Verwerkt spelers in batches voor efficiëntie"""
    setup_complete.wait()
    
    while True:
        try:
            # Verzamel een batch van spelers
            batch = []
            for _ in range(BATCH_SIZE):
                if not priority_queue.empty():
                    priority, player = priority_queue.get()
                    
                    # Check of deze speler nog steeds een update nodig heeft
                    cached_data = data_manager.get_cached_player_data(player['id'])
                    if not cached_data:  # Alleen als niet recent gecached
                        batch.append(player)
                    
                    priority_queue.task_done()
            
            if not batch:
                time.sleep(5)  # Wacht als er geen werk is
                continue
            
            print(f"[BATCH WORKER] Verwerken van {len(batch)} spelers...")
            
            # Verwerk de batch met geoptimaliseerde tab-management
            for player in batch:
                process_player_optimized(driver, player)
                time.sleep(1)  # Korte pauze tussen requests
                
        except Exception as e:
            print(f"[FOUT in Batch Worker]: {e}")
            time.sleep(10)

def process_player_optimized(driver, player):
    """Geoptimaliseerde speler verwerking met hergebruik van tabs"""
    try:
        username = player.get('uname')
        if not username:
            return
            
        print(f"  -> BATCH: Processing {username}...")
        
        # Hergebruik huidige tab in plaats van nieuwe tab maken
        detail_url = USER_DETAIL_URL_TEMPLATE.format(username)
        driver.get(detail_url)
        time.sleep(1.5)  # Verminderde wachttijd
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        response_object = json.loads(soup.find('body').get_text())
        player_details = response_object.get('data', {})
        
        # Cache de volledige player data
        data_manager.cache_player_data(player['id'], username, player_details)
        
        kills = player_details.get('kills', 'N/A')
        shots_obj = player_details.get('bullets_shot', {})
        total_shots = shots_obj.get('total', 'N/A')
        
        print(f"  -> CACHED {username}: Kills={kills}, Shots={total_shots}")
        
    except Exception as e:
        print(f"[FOUT bij verwerking {username}]: {e}")

# --- FLASK ROUTES ---
app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('players'))

@app.route('/players')
def players():
    with data_manager.lock:
        all_users = data_manager.full_user_list
        
        # Sorteer altijd op positie: 1 is hoogste, dan naar beneden
        all_users = sorted(all_users, key=lambda x: x.get('position', 999999))
        
        families = sorted(list(set(user.get('f_name', '') for user in all_users if user.get('f_name'))))
        ranks = sorted(list(set(user.get('rank_name', '') for user in all_users if user.get('rank_name'))))
    
    return render_template('Players.html', 
                         all_users=all_users, 
                         families=families, 
                         ranks=ranks)

@app.route('/families')
def families():
    with data_manager.lock:
        all_users = data_manager.full_user_list
        families = sorted(list(set(user.get('f_name', '') for user in all_users if user.get('f_name'))))
        target_families = data_manager.target_families
    
    return render_template('families.html', 
                         families=families, 
                         target_families=target_families)

@app.route('/set-family-targets', methods=['POST'])
def set_family_targets():
    try:
        families = request.json.get('families', [])
        with data_manager.lock:
            data_manager.target_families = families
        return jsonify({"message": f"Target families ingesteld: {', '.join(families)}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/player-details/<player_id>')
def get_player_details(player_id):
    """API endpoint voor real-time speler details"""
    cached_data = data_manager.get_cached_player_data(player_id)
    if cached_data:
        return jsonify(cached_data)
    else:
        return jsonify({"error": "No cached data available"}), 404

@app.route('/api/player-full/<username>')
def get_player_full_details(username):
    """API endpoint voor volledige speler informatie"""
    try:
        # Zoek speler in cache eerst
        with data_manager.lock:
            for user in data_manager.full_user_list:
                if user.get('uname') == username:
                    cached_data = data_manager.get_cached_player_data(user['id'])
                    if cached_data:
                        return jsonify(cached_data)
                    break
        
        return jsonify({"error": "Player data not available in cache"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """API endpoint voor systeem statistieken"""
    cursor = data_manager.db.execute('SELECT COUNT(*) FROM player_cache')
    cached_players = cursor.fetchone()[0]
    
    return jsonify({
        "cached_players": cached_players,
        "target_families": len(data_manager.target_families),
        "queue_size": priority_queue.qsize(),
        "last_list_update": data_manager.last_list_update.isoformat() if data_manager.last_list_update else None
    })

# --- HOOFDPROGRAMMA ---
if __name__ == "__main__":
    driver = None
    try:
        # Start Flask server
        flask_thread = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False, port=5000, host='127.0.0.1'))
        flask_thread.daemon = True
        flask_thread.start()
        print("\n🌐 Webserver gestart op http://127.0.0.1:5000")
        print("📊 War Intelligence Dashboard geladen!")

        # Start één geoptimaliseerde browser
        print("\n--- CONFIGURATIE GEOPTIMALISEERDE BROWSER ---")
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = uc.Chrome(options=options)
        setup_browser_session(driver, USER_LIST_URL, "Smart Worker")
        
        # Signaal dat setup klaar is
        setup_complete.set()

        # Start de geoptimaliseerde worker threads
        list_thread = threading.Thread(target=smart_list_worker, args=(driver,))
        list_thread.daemon = True
        list_thread.start()
        
        batch_thread = threading.Thread(target=batch_detail_worker, args=(driver,))
        batch_thread.daemon = True
        batch_thread.start()

        print(f"\n--- GEOPTIMALISEERD SYSTEEM ACTIEF ---")
        print(f"🎯 War Intelligence Dashboard: http://127.0.0.1:5000")
        print(f"⚡ Smart List Worker: Detecteert wijzigingen")
        print(f"🔄 Batch Detail Worker: Verwerkt {BATCH_SIZE} spelers per batch")
        print(f"💾 Cache Duration: {CACHE_DURATION} seconden")
        print(f"🗄️ Database: SQLite voor persistente cache")
        print(f"\n🚀 Systeem draait! Open je browser naar: http://127.0.0.1:5000")
        
        while True:
            time.sleep(100)

    except KeyboardInterrupt:
        print("\n\n👋 Script gestopt door gebruiker.")
    except Exception as e:
        print(f"\n❌ Fout: {e}")
    finally:
        if driver:
            driver.quit()
        if hasattr(data_manager, 'db'):
            data_manager.db.close()
        print("🔒 Browser en database verbindingen afgesloten.")