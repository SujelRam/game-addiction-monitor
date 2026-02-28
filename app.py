from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import sqlite3
import time
import threading
import subprocess
import csv
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = Flask(__name__)
app.secret_key = "change_this_secret_key"
app.permanent_session_lifetime = timedelta(days=7)

DB_NAME = "users.db"

# Monitoring state (shared for app + floating bar)
_monitor_lock = threading.Lock()
_monitor_started_at = None
_monitor_elapsed_seconds = 0.0
_monitor_running = False
_monitor_event_hook = None
_monitor_user_id = None
_game_detected = False
_game_title = "No game detected"
_session_game_name = None

GAME_KEYWORDS = (
    "steam",
    "epicgameslauncher",
    "riotclientservices",
    "valorant",
    "leagueclient",
    "dota2",
    "cs2",
    "csgo",
    "fortnite",
    "minecraft",
    "roblox",
    "gta",
    "fifa",
    "efootball",
    "pubg",
)


# ==========================
# DATABASE SETUP
# ==========================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS user_monitor_stats (
            user_id INTEGER PRIMARY KEY,
            total_play_seconds INTEGER NOT NULL DEFAULT 0,
            total_sessions INTEGER NOT NULL DEFAULT 0,
            last_session_seconds INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS game_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_name TEXT NOT NULL,
            play_seconds INTEGER NOT NULL,
            played_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS user_alert_settings (
            user_id INTEGER PRIMARY KEY,
            phone_number TEXT,
            email_alerts_enabled INTEGER NOT NULL DEFAULT 1,
            sms_alerts_enabled INTEGER NOT NULL DEFAULT 0,
            alert_on_game_detect INTEGER NOT NULL DEFAULT 1,
            alert_threshold_minutes INTEGER NOT NULL DEFAULT 30,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            game_name TEXT,
            sent_via TEXT,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


def set_monitor_event_hook(callback):
    """Register desktop-side callback for monitoring events."""
    global _monitor_event_hook
    _monitor_event_hook = callback


def _dispatch_monitor_event(event_name):
    if callable(_monitor_event_hook):
        try:
            _monitor_event_hook(
                event_name,
                {
                    "status": "running" if _monitor_running else "paused",
                    "elapsed_seconds": int(_get_elapsed_seconds()),
                    "game_detected": _game_detected,
                    "game_title": _game_title,
                },
            )
        except Exception:
            pass


def _get_elapsed_seconds():
    with _monitor_lock:
        if _monitor_running and _monitor_started_at is not None:
            return _monitor_elapsed_seconds + (time.monotonic() - _monitor_started_at)
        return _monitor_elapsed_seconds


def _format_elapsed(seconds):
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    sec = total % 60
    return f"{hours:02d}:{minutes:02d}:{sec:02d}"


def _detect_game_running():
    """
    Best-effort game process detection on Windows using tasklist output.
    """
    try:
        output = subprocess.check_output(
            ["tasklist", "/fo", "csv", "/nh"],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        reader = csv.reader(io.StringIO(output))
        for row in reader:
            if not row:
                continue
            process_name = row[0].strip().lower()
            for keyword in GAME_KEYWORDS:
                if keyword in process_name:
                    return True, process_name
        return False, "No game detected"
    except Exception:
        return False, "No game detected"


def _monitor_detection_worker():
    global _game_detected, _game_title, _session_game_name
    while True:
        time.sleep(3)
        with _monitor_lock:
            running = _monitor_running
        if not running:
            continue

        detected, title = _detect_game_running()
        changed = (detected != _game_detected) or (detected and title != _game_title)
        if changed:
            _game_detected = detected
            _game_title = title
            if detected:
                _session_game_name = title
                # Trigger alert when game is detected
                _trigger_game_alert(_monitor_user_id, title)
            _dispatch_monitor_event("game_on" if detected else "game_off")


def get_user_monitor_stats(user_id):
    if not user_id:
        return {
            "total_play_seconds": 0,
            "total_sessions": 0,
            "last_session_seconds": 0,
            "total_play_time_display": "00:00:00",
        }

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT total_play_seconds, total_sessions, last_session_seconds FROM user_monitor_stats WHERE user_id=?",
        (user_id,),
    )
    row = c.fetchone()
    conn.close()

    if not row:
        return {
            "total_play_seconds": 0,
            "total_sessions": 0,
            "last_session_seconds": 0,
            "total_play_time_display": "00:00:00",
        }

    return {
        "total_play_seconds": row[0],
        "total_sessions": row[1],
        "last_session_seconds": row[2],
        "total_play_time_display": _format_elapsed(row[0]),
    }


def _record_monitor_session(user_id, elapsed_seconds, game_name=None):
    if not user_id or elapsed_seconds <= 0:
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO user_monitor_stats (user_id, total_play_seconds, total_sessions, last_session_seconds, updated_at)
        VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            total_play_seconds = total_play_seconds + excluded.total_play_seconds,
            total_sessions = total_sessions + 1,
            last_session_seconds = excluded.last_session_seconds,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, int(elapsed_seconds), int(elapsed_seconds)),
    )
    
    # Record game history if a game was detected
    if game_name:
        c.execute(
            """
            INSERT INTO game_history (user_id, game_name, play_seconds, played_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, game_name, int(elapsed_seconds)),
        )
    
    conn.commit()
    conn.close()


def _monitor_start(user_id=None):
    global _monitor_started_at, _monitor_running, _monitor_user_id, _game_detected, _game_title
    with _monitor_lock:
        if not _monitor_running:
            _monitor_started_at = time.monotonic()
            _monitor_running = True
            if user_id:
                _monitor_user_id = user_id
            _game_detected = False
            _game_title = "No game detected"
    _dispatch_monitor_event("start")


def _monitor_pause():
    global _monitor_started_at, _monitor_elapsed_seconds, _monitor_running
    with _monitor_lock:
        if _monitor_running and _monitor_started_at is not None:
            _monitor_elapsed_seconds += time.monotonic() - _monitor_started_at
            _monitor_started_at = None
            _monitor_running = False
    _dispatch_monitor_event("pause")


def _monitor_stop():
    global _monitor_started_at, _monitor_elapsed_seconds, _monitor_running, _monitor_user_id, _game_detected, _game_title, _session_game_name
    final_elapsed = 0
    owner_id = None
    game_played = _session_game_name
    with _monitor_lock:
        if _monitor_running and _monitor_started_at is not None:
            _monitor_elapsed_seconds += time.monotonic() - _monitor_started_at
        final_elapsed = _monitor_elapsed_seconds
        owner_id = _monitor_user_id
        _monitor_started_at = None
        _monitor_running = False
        _monitor_elapsed_seconds = 0.0
        _monitor_user_id = None
        _game_detected = False
        _game_title = "No game detected"
        _session_game_name = None

    _record_monitor_session(owner_id, final_elapsed, game_played)
    _dispatch_monitor_event("stop")


# ==========================
# ALERT SYSTEM FUNCTIONS
# ==========================

def get_user_alert_settings(user_id):
    """Get alert settings for a user."""
    if not user_id:
        return None
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """SELECT phone_number, email_alerts_enabled, sms_alerts_enabled, 
           alert_on_game_detect, alert_threshold_minutes 
           FROM user_alert_settings WHERE user_id=?""",
        (user_id,),
    )
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {
            "phone_number": "",
            "email_alerts_enabled": True,
            "sms_alerts_enabled": False,
            "alert_on_game_detect": True,
            "alert_threshold_minutes": 30
        }
    
    return {
        "phone_number": row[0] or "",
        "email_alerts_enabled": bool(row[1]),
        "sms_alerts_enabled": bool(row[2]),
        "alert_on_game_detect": bool(row[3]),
        "alert_threshold_minutes": row[4]
    }


def save_user_alert_settings(user_id, settings):
    """Save alert settings for a user."""
    if not user_id:
        return False
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO user_alert_settings 
        (user_id, phone_number, email_alerts_enabled, sms_alerts_enabled, 
         alert_on_game_detect, alert_threshold_minutes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            phone_number = excluded.phone_number,
            email_alerts_enabled = excluded.email_alerts_enabled,
            sms_alerts_enabled = excluded.sms_alerts_enabled,
            alert_on_game_detect = excluded.alert_on_game_detect,
            alert_threshold_minutes = excluded.alert_threshold_minutes,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            settings.get("phone_number", ""),
            1 if settings.get("email_alerts_enabled", True) else 0,
            1 if settings.get("sms_alerts_enabled", False) else 0,
            1 if settings.get("alert_on_game_detect", True) else 0,
            settings.get("alert_threshold_minutes", 30),
        ),
    )
    conn.commit()
    conn.close()
    return True


def get_alerts_log(user_id, limit=20):
    """Get alert history for a user."""
    if not user_id:
        return []
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """SELECT alert_type, message, game_name, sent_via, sent_at 
           FROM alerts_log WHERE user_id = ? ORDER BY sent_at DESC LIMIT ?""",
        (user_id, limit),
    )
    rows = c.fetchall()
    conn.close()
    
    alerts = []
    for row in rows:
        alerts.append({
            "alert_type": row[0],
            "message": row[1],
            "game_name": row[2],
            "sent_via": row[3],
            "sent_at": row[4]
        })
    return alerts


def _send_alert(user_id, alert_type, message, game_name=None, sent_via=None):
    """Send an alert and log it. This is a simulated function - logs to database."""
    if not user_id:
        return False
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """INSERT INTO alerts_log (user_id, alert_type, message, game_name, sent_via, sent_at)
           VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
        (user_id, alert_type, message, game_name, sent_via),
    )
    conn.commit()
    conn.close()
    
    # Real email sending (only if sent_via == "email")
    if sent_via == "email":
        try:
            # Import secure email configuration
            from email_config import get_email_config, is_email_configured
            
            # Check if email is configured
            if not is_email_configured():
                print(f"[EMAIL ERROR] Email not configured! Please set up your Gmail credentials in email_config.py")
                print(f"[EMAIL ERROR] See email_config.py for instructions on how to set up Gmail App Password")
                return False
            
            # Get email configuration
            email_config = get_email_config()
            sender_email = email_config['email']
            sender_password = email_config['app_password']
            
            # Get recipient email from database
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT email FROM users WHERE id=?", (user_id,))
            row = c.fetchone()
            conn.close()
            recipient_email = row[0] if row else None
            
            if recipient_email:
                subject = f"Game Addiction Monitor Alert: {alert_type}"
                msg = MIMEMultipart()
                msg["From"] = sender_email
                msg["To"] = recipient_email
                msg["Subject"] = subject
                msg.attach(MIMEText(message, "plain"))
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
                server.quit()
                print(f"[EMAIL SENT] to {recipient_email}: {subject} - {message}")
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")
    # For now, we just log to database and print to console
    print(f"[ALERT] User {user_id}: {alert_type} - {message}")
    return True


def _trigger_game_alert(user_id, game_name):
    """Trigger alert when a game is detected."""
    if not user_id:
        return
    
    settings = get_user_alert_settings(user_id)
    
    if not settings or not settings.get("alert_on_game_detect"):
        return
    
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"Game detected: {game_name} at {current_time}"
    
    # Send email alert if enabled
    if settings.get("email_alerts_enabled"):
        _send_alert(user_id, "game_detected", message, game_name, "email")
    
    # Send SMS alert if enabled and phone number is provided
    if settings.get("sms_alerts_enabled") and settings.get("phone_number"):
        _send_alert(user_id, "game_detected", message, game_name, "sms")


# ==========================
# MONITORING WORKER
# ==========================

_monitor_worker_thread = threading.Thread(target=_monitor_detection_worker, daemon=True)
_monitor_worker_thread.start()


# ==========================
# LANDING PAGE
# ==========================

@app.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")


# ==========================
# REGISTER
# ==========================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        created_user_id = None

        try:
            c.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password),
            )
            created_user_id = c.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Email already exists"

        conn.close()

        session.permanent = True
        session["user"] = {"id": created_user_id, "name": name, "email": email}

        return redirect(url_for("dashboard"))

    return render_template("register.html")


# ==========================
# LOGIN
# ==========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name, email, password FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session.permanent = True
            session["user"] = {"id": user[0], "name": user[1], "email": user[2]}
            return redirect(url_for("dashboard"))
        return "Invalid credentials"

    return render_template("login.html")


# ==========================
# DASHBOARD (Protected)
# ==========================

@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("login"))

    monitor_stats = get_user_monitor_stats(session["user"].get("id"))
    return render_template(
        "dashboard.html",
        user=session["user"],
        monitor_stats=monitor_stats,
        monitor_state="running" if _monitor_running else "paused",
    )


@app.route("/monitor-bar")
def monitor_bar():
    """
    Separate compact bar shown in a top-most window by PyWebView.
    Not intended for public browser usage.
    """
    return render_template("monitor_bar.html")


# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/stats")
def stats():
    if not session.get("user"):
        return redirect(url_for("login"))

    return jsonify({"today_hours": 4.5, "weekly_avg": 3.2, "risk": "At Risk"})


@app.route("/api/monitor/status")
def monitor_status():
    elapsed = _get_elapsed_seconds()
    current_user = session.get("user", {})
    user_stats = get_user_monitor_stats(current_user.get("id"))
    return jsonify(
        {
            "status": "running" if _monitor_running else "paused",
            "elapsed_seconds": int(elapsed),
            "elapsed_display": _format_elapsed(elapsed),
            "game_detected": _game_detected,
            "game_title": _game_title,
            "total_sessions": user_stats["total_sessions"],
            "total_play_time_display": user_stats["total_play_time_display"],
        }
    )


@app.route("/api/monitor/start", methods=["POST"])
def monitor_start():
    user = session.get("user", {})
    _monitor_start(user.get("id"))
    elapsed = _get_elapsed_seconds()
    return jsonify(
        {
            "ok": True,
            "message": "Monitoring started.",
            "status": "running",
            "elapsed_display": _format_elapsed(elapsed),
            "game_detected": _game_detected,
            "game_title": _game_title,
        }
    )


@app.route("/api/monitor/pause", methods=["POST"])
def monitor_pause():
    _monitor_pause()
    elapsed = _get_elapsed_seconds()
    return jsonify(
        {
            "ok": True,
            "message": "Monitoring paused.",
            "status": "paused",
            "elapsed_display": _format_elapsed(elapsed),
            "game_detected": _game_detected,
            "game_title": _game_title,
        }
    )


@app.route("/api/monitor/stop", methods=["POST"])
def monitor_stop():
    user = session.get("user", {})
    _monitor_stop()
    user_stats = get_user_monitor_stats(user.get("id"))
    return jsonify(
        {
            "ok": True,
            "message": "Monitoring stopped.",
            "status": "paused",
            "elapsed_display": "00:00:00",
            "game_detected": _game_detected,
            "game_title": _game_title,
            "total_sessions": user_stats["total_sessions"],
            "total_play_time_display": user_stats["total_play_time_display"],
        }
    )


@app.route("/api/monitor/game-history")
def game_history():
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session["user"].get("id")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT game_name, play_seconds, played_at FROM game_history WHERE user_id = ? ORDER BY played_at DESC LIMIT 20",
        (user_id,),
    )
    rows = c.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "game_name": row[0],
            "play_time": _format_elapsed(row[1]),
            "played_at": row[2]
        })
    
    return jsonify({"history": history})


# ==========================
# ALERT API ROUTES
# ==========================

@app.route("/api/alerts/settings", methods=["GET"])
def alerts_settings_get():
    """Get user's alert settings."""
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session["user"].get("id")
    settings = get_user_alert_settings(user_id)
    return jsonify(settings)


@app.route("/api/alerts/settings", methods=["POST"])
def alerts_settings_save():
    """Save user's alert settings."""
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session["user"].get("id")
    data = request.get_json()
    
    success = save_user_alert_settings(user_id, data)
    if success:
        return jsonify({"ok": True, "message": "Alert settings saved"})
    return jsonify({"ok": False, "error": "Failed to save settings"}), 500


@app.route("/api/alerts/log", methods=["GET"])
def alerts_log_get():
    """Get alert history for the user."""
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session["user"].get("id")
    alerts = get_alerts_log(user_id)
    return jsonify({"alerts": alerts})


@app.route("/api/alerts/test", methods=["POST"])
def alerts_test():
    """Send a test alert."""
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session["user"].get("id")
    user = session["user"]
    
    message = f"Test alert from Game Addiction Monitor. User: {user.get('name')}"
    
    # Get settings to determine where to send
    settings = get_user_alert_settings(user_id)
    
    sent = False
    if settings.get("email_alerts_enabled"):
        _send_alert(user_id, "test", message, None, "email")
        sent = True
    
    if settings.get("sms_alerts_enabled") and settings.get("phone_number"):
        _send_alert(user_id, "test", message, None, "sms")
        sent = True
    
    if not sent:
        # Even if no channels enabled, log a test alert
        _send_alert(user_id, "test", message, None, "system")
    
    return jsonify({"ok": True, "message": "Test alert sent"})


@app.route("/api/alerts/email-status", methods=["GET"])
def alerts_email_status():
    """Check if email is configured."""
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 401
    
    from email_config import is_email_configured, get_email_config
    
    configured = is_email_configured()
    email = None
    
    if configured:
        config = get_email_config()
        if config:
            # Return masked email
            email = config.get('email', '')
            if email and '@' in email:
                parts = email.split('@')
                email = parts[0][:2] + '***@' + parts[1] if len(parts[0]) > 2 else '***@' + parts[1]
    
    return jsonify({
        "configured": configured,
        "email": email
    })


@app.route("/api/alerts/email-config", methods=["POST"])
def alerts_email_config():
    """Save email configuration."""
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    gmail_email = data.get('email', '').strip()
    gmail_app_password = data.get('app_password', '').strip()
    
    if not gmail_email or not gmail_app_password:
        return jsonify({"ok": False, "error": "Email and App Password are required"}), 400
    
    # Validate Gmail format
    if not gmail_email.endswith('@gmail.com'):
        return jsonify({"ok": False, "error": "Please enter a valid Gmail address"}), 400
    
    # Save to environment variables (session only) or config file
    import os
    os.environ['GMAIL_EMAIL'] = gmail_email
    os.environ['GMAIL_APP_PASSWORD'] = gmail_app_password
    
    # Test the connection
    try:
        from email_config import get_email_config, is_email_configured
        
        if is_email_configured():
            # Try to send a test email to verify
            config = get_email_config()
            test_msg = MIMEMultipart()
            test_msg["From"] = config['email']
            test_msg["To"] = config['email']
            test_msg["Subject"] = "Game Addiction Monitor - Email Configuration Test"
            test_msg.attach(MIMEText("Your email configuration is working correctly!", "plain"))
            
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(config['email'], config['app_password'])
            server.sendmail(config['email'], config['email'], test_msg.as_string())
            server.quit()
            
            return jsonify({"ok": True, "message": "Email configured successfully! Test email sent."})
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to connect: {str(e)}"}), 500


@app.route("/api/alerts/test-email-connection", methods=["POST"])
def alerts_test_email_connection():
    """Test email connection."""
    if not session.get("user"):
        return jsonify({"error": "Not logged in"}), 401
    
    from email_config import is_email_configured
    
    if not is_email_configured():
        return jsonify({"ok": False, "error": "Email not configured"}), 400
    
    try:
        from email_config import get_email_config
        config = get_email_config()
        
        # Send test email to self
        test_msg = MIMEMultipart()
        test_msg["From"] = config['email']
        test_msg["To"] = config['email']
        test_msg["Subject"] = "Game Addiction Monitor - Connection Test"
        test_msg.attach(MIMEText("Your email settings are working correctly! You will receive alerts when games are detected.", "plain"))
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(config['email'], config['app_password'])
        server.sendmail(config['email'], config['email'], test_msg.as_string())
        server.quit()
        
        return jsonify({"ok": True, "message": "Email connection successful! Test email sent."})
    except Exception as e:
        return jsonify({"ok": False, "error": f"Connection failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
