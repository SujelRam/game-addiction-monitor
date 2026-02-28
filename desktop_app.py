"""
Desktop launcher for Flask app using PyWebView
"""

import threading
import time
import webview
import app as flask_backend


main_window = None
monitor_bar_window = None


def run_flask():
    flask_backend.app.run(
        debug=False,
        host="127.0.0.1",
        port=5000,
        use_reloader=False
    )


def monitor_event_handler(event_name, payload):
    """
    Receives monitor events from Flask and updates floating top bar.
    """
    global monitor_bar_window

    if monitor_bar_window is None:
        return

    status = payload.get("status", "paused")
    elapsed_seconds = int(payload.get("elapsed_seconds", 0))

    hours = elapsed_seconds // 3600
    minutes = (elapsed_seconds % 3600) // 60
    seconds = elapsed_seconds % 60
    elapsed_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # Show bar when monitoring starts, keep on top.
    if event_name == "start":
        try:
            monitor_bar_window.show()
            monitor_bar_window.bring_to_front()
        except Exception:
            pass
    elif event_name == "stop":
        try:
            monitor_bar_window.hide()
        except Exception:
            pass

    # Keep compact bar state synchronized.
    try:
        game_detected = payload.get("game_detected", False)
        game_title = payload.get("game_title", "No game detected")
        safe_game_title = str(game_title).replace("\\", "\\\\").replace("'", "\\'")
        js = (
            f"document.getElementById('barStatus').textContent = '{status.upper()}';"
            f"document.getElementById('barStatus').style.color = "
            f"'{('#22c55e' if status == 'running' else '#f59e0b')}';"
            f"document.getElementById('barTimer').textContent = '{elapsed_display}';"
            f"document.getElementById('barGameState').textContent = "
            f"'{('Playing: ' + safe_game_title) if game_detected else 'No game detected'}';"
        )
        monitor_bar_window.evaluate_js(js)
    except Exception:
        pass


def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    time.sleep(1.5)

    flask_backend.set_monitor_event_hook(monitor_event_handler)

    global main_window, monitor_bar_window
    main_window = webview.create_window(
        "AI Powered Game Addiction Monitor",
        "http://127.0.0.1:5000",
        width=1200,
        height=800,
        resizable=True
    )

    # Compact floating monitoring bar shown above all applications.
    monitor_bar_window = webview.create_window(
        "Monitoring Bar",
        "http://127.0.0.1:5000/monitor-bar",
        width=560,
        height=76,
        x=500,
        y=20,
        frameless=True,
        on_top=True,
        easy_drag=True,
        resizable=False,
        hidden=True
    )

    webview.start()


if __name__ == "__main__":
    main()
