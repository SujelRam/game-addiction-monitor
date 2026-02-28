# Sample Coding - AI Powered Online Game Addiction Monitor and Alert System

---

## 1. Main Application (app.py)

```
python
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, time, threading, subprocess, csv, io

app = Flask(__name__)
app.secret_key = "change_this_key"

# Game process keywords
GAME_KEYWORDS = ("steam", "valorant", "minecraft", "roblox", "fortnite", "cs2", "dota2", "gta")

# Monitoring state
_monitor_lock = threading.Lock()
_monitor_started_at = None
_monitor_elapsed = 0.0
_monitor_running = False
_game_detected = False

# ============= DATABASE =============
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_stats (user_id PRIMARY KEY, total_seconds INTEGER DEFAULT 0, sessions INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS game_history (id INTEGER PRIMARY KEY, user_id INTEGER, game_name TEXT, play_seconds INTEGER, played_at TEXT)""")
    conn.commit()
    conn.close()

init_db()

# ============= GAME DETECTION =============
def detect_game():
    try:
        output = subprocess.check_output(["tasklist", "/fo", "csv", "/nh"], text=True)
        for row in csv.reader(io.StringIO(output)):
            if row:
                proc = row[0].strip().lower()
                for kw in GAME_KEYWORDS:
                    if kw in proc: return True, proc
    except: pass
    return False, "No game"

# ============= MONITORING =============
def monitor_worker():
    global _game_detected
    while True:
        time.sleep(3)
        with _monitor_lock:
            if not _monitor_running: continue
        detected, title = detect_game()
        if detected != _game_detected:
            _game_detected = detected

threading.Thread(target=monitor_worker, daemon=True).start()

@app.route("/")
def index(): return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    name, email, pwd = request.form["name"], request.form["email"], generate_password_hash(request.form["password"])
    conn = sqlite3.connect("users.db")
    try:
        conn.execute("INSERT INTO users (name, email, password) VALUES (?,?,?)", (name, email, pwd))
        conn.commit()
    except: return "Email exists"
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/login", methods=["POST"])
def login():
    email, pwd = request.form["email"], request.form["password"]
    conn = sqlite3.connect("users.db")
    user = conn.execute("SELECT id, name, password FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    if user and check_password_hash(user[2], pwd):
        session["user"] = {"id": user[0], "name": user[1]}
        return redirect(url_for("dashboard"))
    return "Invalid"

@app.route("/dashboard")
def dashboard():
    if not session.get("user"): return redirect(url_for("login"))
    stats = conn.execute("SELECT total_seconds, sessions FROM user_stats WHERE user_id=?", (session["user"]["id"],)).fetchone()
    return render_template("dashboard.html", user=session["user"], stats=stats or [0,0])

@app.route("/api/start", methods=["POST"])
def start_monitor():
    global _monitor_started_at, _monitor_running
    with _monitor_lock:
        _monitor_started_at = time.monotonic()
        _monitor_running = True
    return jsonify({"status": "running"})

@app.route("/api/stop", methods=["POST"])
def stop_monitor():
    global _monitor_started_at, _monitor_running, _monitor_elapsed
    with _monitor_lock:
        if _monitor_running:
            _monitor_elapsed += time.monotonic() - _monitor_started_at
        _monitor_running = False
    conn = sqlite3.connect("users.db")
    conn.execute("INSERT INTO user_stats (user_id, total_seconds, sessions) VALUES (?,?,1) ON CONFLICT DO UPDATE SET total_seconds=total_seconds+?, sessions=sessions+1", 
                 (session["user"]["id"], int(_monitor_elapsed), int(_monitor_elapsed)))
    conn.commit()
    conn.close()
    _monitor_elapsed = 0
    return jsonify({"status": "stopped"})

if __name__ == "__main__": app.run(debug=True)
```

---

## 2. AI Analysis Module (model.py)

```
python
class GameAddictionAnalyzer:
    def __init__(self):
        self.NORMAL_HOURS = 2
        self.RISK_HOURS = 4

    def analyze(self, hours, sessions, night_play):
        score = 0
        factors = []
        
        # Hours factor
        if hours > self.RISK_HOURS: score += 60; factors.append("Excessive hours")
        elif hours > self.NORMAL_HOURS: score += 40; factors.append("Moderate hours")
        else: score += 10
        
        # Sessions factor
        if sessions > 3: score += 30; factors.append("Many sessions")
        elif sessions > 1: score += 20; factors.append("Several sessions")
        
        # Night play factor
        if night_play == 'yes': score += 15; factors.append("Night gaming")
        
        # Classification
        if score <= 30: level = "Normal"
        elif score <= 60: level = "At Risk"
        else: level = "Addicted"
        
        return {'level': level, 'score': min(score,100), 'factors': factors}

# Test
if __name__ == "__main__":
    a = GameAddictionAnalyzer()
    print(a.analyze(3.5, 3, 'yes'))
    # Output: {'level': 'Addicted', 'score': 75, 'factors': ['Moderate hours', 'Many sessions', 'Night gaming']}
```

---

## 3. Desktop App (desktop_app.py)

```
python
import threading, time, webview, app as backend

def run_flask():
    backend.app.run(host="127.0.0.1", port=5000, use_reloader=False)

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(1)
    
    main_win = webview.create_window("Game Monitor", "http://127.0.0.1:5000", width=1000, height=700)
    bar_win = webview.create_window("Bar", "http://127.0.0.1:5000/bar", width=500, height=60, frameless=True, on_top=True, hidden=True)
    
    webview.start()

if __name__ == "__main__": main()
```

---

## 4. Email Config (email_config.py)

```
python
import os

def get_config():
    return {
        'email': os.environ.get('GMAIL_EMAIL', 'your_email@gmail.com'),
        'password': os.environ.get('GMAIL_APP_PASSWORD', 'your_password')
    }

def is_configured():
    c = get_config()
    return c['email'] != 'your_email@gmail.com'
```

---

