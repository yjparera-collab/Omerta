#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB Scraping Service (Windows Visible Browser)
- Robust parsing for Barafranca APIs (users + user&name=...)
- Handles Cloudflare via visible undetected-chromedriver
- Caches both list and detail payloads in MongoDB
- Resolves user_id from username using the latest list/cache when missing
- Normalizes detective target output with real values (no fake defaults)
- Notifies FastAPI backend for realtime UI refresh after cache updates
"""
import os
import time
import json
import random
import threading
from datetime import datetime
from queue import PriorityQueue

from flask import Flask, jsonify, request
from bs4 import BeautifulSoup
from pymongo import MongoClient
from dotenv import load_dotenv
import undetected_chromedriver as uc
import requests

# -------------------- ENV --------------------
load_dotenv()
USER_LIST_URL = "https://barafranca.com/index.php?module=API&action=users"
USER_DETAIL_URL_TEMPLATE = "https://barafranca.com/index.php?module=API&action=user&name={}" 
MAIN_LIST_INTERVAL = 30

# -------------------- MONGO --------------------
def init_mongodb():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://127.0.0.1:27017')
    client = MongoClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'omerta_intelligence')]
    print(f"[DB] Connected to MongoDB: {mongo_url}")
    print(f"[DB] Database: {db.name}")
    # Indexes
    try:
        db.detective_targets.create_index("username", unique=True)
        db.detective_targets.create_index("is_active")
        db.player_cache.create_index("user_id", unique=True)
        db.intelligence_notifications.create_index("timestamp")
    except Exception as e:
        print(f"[DB] Index warning: {e}")
    return db

# -------------------- DATA MANAGER --------------------
class IntelligenceDataManager:
    def __init__(self):
        self.db = init_mongodb()
        self.full_user_list = []   # list of normalized player dicts from users API
        self.detective_targets = set()
        self.notification_callbacks = []
        self.lock = threading.Lock()
        self.load_detective_targets()

    def load_detective_targets(self):
        try:
            targets = list(self.db.detective_targets.find({"is_active": True}))
            self.detective_targets = {t['username'] for t in targets}
            print(f"[TARGET] Loaded {len(self.detective_targets)} detective targets")
        except Exception as e:
            print(f"[TARGET] Load error: {e}")

    def add_detective_targets(self, usernames):
        added = 0
        for username in usernames:
            try:
                res = self.db.detective_targets.update_one(
                    {"username": username},
                    {"$set": {"username": username, "is_active": True, "added_timestamp": datetime.utcnow()}},
                    upsert=True
                )
                if res.upserted_id or res.modified_count > 0:
                    self.detective_targets.add(username)
                    added += 1
            except Exception as e:
                print(f"[TARGET] Add error for {username}: {e}")
        return {"added": added, "total": len(self.detective_targets)}

    def get_user_id_by_username(self, username: str):
        """Resolve user_id from latest list or cache; returns str or None"""
        if not username:
            return None
        try:
            name_l = str(username).lower()
            # Prefer latest list (normalized)
            for user in self.full_user_list or []:
                u = user.get('uname') or user.get('username') or user.get('name')
                if u and str(u).lower() == name_l:
                    uid = user.get('user_id') or user.get('id') or user.get('player_id')
                    if uid is not None:
                        return str(uid)
            # Fallback to cache
            doc = self.db.player_cache.find_one({"username": username})
            if doc and doc.get('user_id'):
                return str(doc['user_id'])
        except Exception as e:
            print(f"[MAP] Failed mapping for {username}: {e}")
        return None

    def cache_player_data(self, user_id: str, username: str, data: dict):
        try:
            doc = {
                "user_id": str(user_id),
                "username": username or f"Player_{user_id}",
                "data": json.dumps(data, default=str),
                "last_updated": datetime.utcnow(),
                "priority": 1,
            }
            self.db.player_cache.update_one({"user_id": str(user_id)}, {"$set": doc}, upsert=True)
            return True
        except Exception as e:
            print(f"[CACHE] Error for {username} ({user_id}): {e}")
            return False

    def notify_backend_list_updated(self, payload=None):
        try:
            backend_url = os.environ.get('BACKEND_URL', 'http://127.0.0.1:8001')
            data = payload or {"source": "scraper", "timestamp": datetime.utcnow().isoformat()}
            requests.post(f"{backend_url}/api/internal/list-updated", json=data, timeout=2)
        except Exception as e:
            # Backend mogelijk elders; dit mag scraper niet blokkeren
            if 'ConnectionRefusedError' not in str(e):
                print(f"[NOTIFY] Backend notify failed: {e}")

    def get_detective_targets(self):
        """Return detective targets with real values if cached; no fake defaults"""
        try:
            targets = list(self.db.detective_targets.find({"is_active": True}))
            result = []
            for t in targets:
                rec = {
                    "username": t['username'],
                    "player_id": t.get('player_id', ''),
                    "added_timestamp": t.get('added_timestamp')
                }
                cached = self.db.player_cache.find_one({"username": t['username']})
                if cached:
                    try:
                        raw = cached.get('data')
                        raw = json.loads(raw) if isinstance(raw, str) else raw
                        inner = raw.get('data', raw) if isinstance(raw, dict) else raw
                        if isinstance(inner, dict):
                            bs = inner.get('bullets_shot')
                            shots_total = bs.get('total') if isinstance(bs, dict) else bs
                            if inner.get('kills') is not None:
                                rec['kills'] = _to_int(inner.get('kills'))
                            if shots_total is not None:
                                rec['shots'] = _to_int(shots_total)
                            if inner.get('wealth') is not None:
                                rec['wealth'] = _to_int(inner.get('wealth'))
                            if inner.get('plating') is not None:
                                rec['plating'] = inner.get('plating')
                            rec['last_updated'] = cached.get('last_updated')
                    except Exception as e:
                        print(f"[TARGETS] Parse error for {t['username']}: {e}")
                result.append(rec)
            return result
        except Exception as e:
            print(f"[TARGETS] Error: {e}")
            return []

# -------------------- BROWSER --------------------
def create_browser():
    print("[BROWSER] Setting up visible Chrome (undetected)")
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--window-size=1366,768')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36')
    try:
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
    except Exception:
        pass
    driver = uc.Chrome(options=options)
    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception:
        pass
    return driver

# -------------------- CLOUDFLARE HELPER --------------------
def smart_cloudflare_handler(driver, url, worker_name, timeout=60):
    print(f"[{worker_name}] Navigating to: {url}")
    try:
        driver.get(url)
        time.sleep(3)
        src = driver.page_source.lower()
        if any(k in src for k in ["cloudflare", "just a moment", "checking your browser"]):
            print("🔒 Cloudflare gedetecteerd, wachten en evt. handmatig helpen…")
            start = time.time()
            while time.time() - start < timeout:
                time.sleep(2)
                try:
                    cur = driver.page_source.lower()
                    if not any(k in cur for k in ["cloudflare", "just a moment", "checking your browser"]):
                        print("✅ Cloudflare gepasseerd")
                        return True
                except Exception:
                    pass
            print("⏰ Time-out bereikt; ga door")
            return False
        else:
            print("✅ Geen Cloudflare - direct toegang!")
            return True
    except Exception as e:
        print(f"[{worker_name}] Error: {e}")
        return False

# -------------------- FLASK --------------------
app = Flask(__name__)
DM = IntelligenceDataManager()
PQ = PriorityQueue()

@app.route('/api/scraping/status')
def status():
    try:
        return jsonify({
            "status": "online",
            "cached_players": DM.db.player_cache.count_documents({}),
            "detective_targets": len(DM.detective_targets),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/players')
def get_players():
    """Return normalized players list for UI (id/uname/rank_name/f_name/status/position/plating)."""
    try:
        docs = list(DM.db.player_cache.find({}, {"_id": 0}).sort("last_updated", -1).limit(2000))
        out = []
        for d in docs:
            try:
                raw = d.get('data')
                raw = json.loads(raw) if isinstance(raw, str) else raw
                inner = raw.get('data', raw) if isinstance(raw, dict) else raw
                if not isinstance(inner, dict):
                    continue
                # Prefer normalized fields, fall back from detail
                uid = inner.get('id') or inner.get('user_id') or d.get('user_id')
                uname = inner.get('uname') or inner.get('username') or inner.get('name') or d.get('username')
                rank_name = inner.get('rank_name') or inner.get('rank')
                f_name = inner.get('f_name') or ((inner.get('family') or {}).get('name') if isinstance(inner.get('family'), dict) else None)
                status_v = inner.get('status')
                position = inner.get('position')
                plating = inner.get('plating')
                if uid and uname:
                    out.append({
                        "id": str(uid),
                        "uname": uname,
                        "rank_name": rank_name,
                        "f_name": f_name,
                        "status": status_v,
                        "position": position,
                        "plating": plating,
                    })
            except Exception:
                continue
        return jsonify({"players": out, "count": len(out), "timestamp": datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/player/<player_id>')
def get_player(player_id):
    try:
        d = DM.db.player_cache.find_one({"user_id": str(player_id)}, {"_id": 0})
        if not d:
            return jsonify({"error": "Player not found"}), 404
        raw = d.get('data')
        raw = json.loads(raw) if isinstance(raw, str) else raw
        inner = raw.get('data', raw) if isinstance(raw, dict) else raw
        if not isinstance(inner, dict):
            return jsonify({"error": "Invalid player data"}), 500
        return jsonify(inner)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/detective/targets')
def get_targets():
    try:
        targets = DM.get_detective_targets()
        return jsonify({
            "tracked_players": targets,
            "count": len(targets),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraping/detective/add', methods=['POST'])
def add_targets():
    try:
        data = request.get_json(force=True) or {}
        usernames = data.get('usernames', [])
        if not usernames:
            return jsonify({"error": "No usernames provided"}), 400
        result = DM.add_detective_targets(usernames)
        return jsonify({"message": f"Added {result['added']} detective targets", "added": result['added'], "total_targets": result['total'], "timestamp": datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------- WORKERS --------------------
def list_worker(driver: uc.Chrome):
    while True:
        try:
            print("\n[LIST_WORKER] Fetching user list...")
            if smart_cloudflare_handler(driver, USER_LIST_URL, "LIST_WORKER", timeout=45):
                time.sleep(1)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                text = soup.text.strip()
                try:
                    users_data = json.loads(text)
                except json.JSONDecodeError as e:
                    print(f"[LIST_WORKER] JSON parse error: {e}")
                    users_data = []

                player_list = []
                if isinstance(users_data, list):
                    player_list = users_data
                    print(f"[LIST_WORKER] ✅ Got list: {len(player_list)} players")
                elif isinstance(users_data, dict):
                    print(f"[LIST_WORKER] 📊 Got dict format, keys: {list(users_data.keys())}")
                    container = users_data.get('data', users_data)
                    if isinstance(container, list):
                        player_list = container
                    elif isinstance(container, dict):
                        if 'users' in container:
                            player_list = container['users']
                        elif 'players' in container:
                            player_list = container['players']
                        else:
                            # collect any dicts that look like players
                            for _, value in container.items():
                                if isinstance(value, dict) and ('user_id' in value or 'id' in value or 'uname' in value or 'username' in value):
                                    player_list.append(value)
                                elif isinstance(value, list):
                                    player_list.extend(value)
                    print(f"[LIST_WORKER] ✅ Extracted {len(player_list) if isinstance(player_list, list) else 0} players from wrapper")
                else:
                    print("[LIST_WORKER] ⚠️ Unexpected data format")

                # Normalize + cache
                cached, failed = 0, 0
                normalized_list = []
                for user in player_list or []:
                    if not isinstance(user, dict):
                        continue
                    uid = user.get('user_id') or user.get('id') or user.get('player_id')
                    if uid is None:
                        # some list entries use different keys; try best-effort
                        uid = user.get('Id') or user.get('UserId')
                    uname = user.get('uname') or user.get('username') or user.get('name')
                    rank_name = user.get('rank_name') or user.get('rank')
                    f_name = user.get('f_name') or ((user.get('family') or {}).get('name') if isinstance(user.get('family'), dict) else None)
                    status_v = user.get('status')
                    position = user.get('position')
                    plating = user.get('plating')
                    if uid and uname:
                        normalized = {
                            "id": str(uid),
                            "user_id": str(uid),
                            "uname": uname,
                            "rank_name": rank_name,
                            "f_name": f_name,
                            "status": status_v,
                            "position": position,
                            "plating": plating,
                        }
                        if DM.cache_player_data(str(uid), uname, normalized):
                            cached += 1
                            normalized_list.append(normalized)
                    else:
                        failed += 1
                DM.full_user_list = normalized_list
                print(f"[LIST_WORKER] 💾 Cached {cached} players, {failed} failed")
            else:
                print("[LIST_WORKER] ❌ Failed to bypass Cloudflare")
        except Exception as e:
            print(f"[LIST_WORKER] ❌ Error: {e}")
        print(f"[LIST_WORKER] ⏳ Next update in {MAIN_LIST_INTERVAL} seconds")
        time.sleep(MAIN_LIST_INTERVAL)


def detail_worker(driver: uc.Chrome):
    while True:
        try:
            if not DM.detective_targets:
                print("[DETAIL_WORKER] ℹ️ No detective targets configured")
            for username in list(DM.detective_targets):
                try:
                    print(f"\n[DETAIL_WORKER] Getting {username}...")
                    url = USER_DETAIL_URL_TEMPLATE.format(username)
                    if smart_cloudflare_handler(driver, url, "DETAIL_WORKER", timeout=45):
                        time.sleep(1)
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        text = soup.text.strip()
                        if text.startswith('{'):
                            user_data = json.loads(text)
                            if isinstance(user_data, dict):
                                inner = user_data.get('data', user_data)
                                uid = user_data.get('user_id') or inner.get('user_id')
                                if not uid:
                                    uid = DM.get_user_id_by_username(username)
                                    if uid:
                                        inner['user_id'] = uid
                                if uid:
                                    if DM.cache_player_data(str(uid), username, inner):
                                        print(f"[DETAIL_WORKER] ✅ Updated data for {username} (id={uid})")
                                        DM.notify_backend_list_updated({"username": username, "user_id": str(uid)})
                                else:
                                    print(f"[DETAIL_WORKER] ⚠️ No user_id for {username} - cached detail skipped")
                    # be polite
                    time.sleep(random.uniform(3, 6))
                except Exception as e:
                    print(f"[DETAIL_WORKER] ❌ Error processing {username}: {e}")
        except Exception as e:
            print(f"[DETAIL_WORKER] ❌ Worker error: {e}")
        print("[DETAIL_WORKER] ⏳ Next batch in 90 seconds")
        time.sleep(90)

# -------------------- MAIN --------------------
if __name__ == '__main__':
    driver = None
    try:
        print("\n[SETUP] Starting MongoDB Omerta Scraping Service (Windows Visible Browser)…")
        # Start Flask in a thread
        svr = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False, port=5001, host='127.0.0.1'))
        svr.daemon = True
        svr.start()
        print("[WEB] Flask scraping API on http://127.0.0.1:5001")

        driver = create_browser()
        print("[BROWSER] ✅ Visible Chrome ready")

        t1 = threading.Thread(target=list_worker, args=(driver,))
        t1.daemon = True
        t1.start()

        t2 = threading.Thread(target=detail_worker, args=(driver,))
        t2.daemon = True
        t2.start()

        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 Stopped by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass
        print("[SECURE] Browser closed")

# -------------------- HELPERS --------------------
def _to_int(v):
    try:
        return int(v)
    except Exception:
        try:
            return int(float(v))
        except Exception:
            return None