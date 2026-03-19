from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
from .db import get_connection
import time
import socket

app = Flask(__name__)
# Enable CORS for all routes to allow browser extensions to communicate
CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"])

@app.route("/tab_update", methods=["POST"])
def tab_update():
    try:
        data = request.json
        conn = get_connection()
        c = conn.cursor()
        
        # Handle both old format (without duration) and new format (with duration)
        timestamp = time.time()
        app = data.get("app")
        title = data.get("title")
        url = data.get("url")
        duration = data.get("duration", 0)  # Default to 0 if not provided
        
        # Insert the tab data
        c.execute("INSERT INTO logs VALUES (?, ?, ?, ?)",
                  (timestamp, app, title, url))
        conn.commit()
        conn.close()
        
        # Log the duration if provided
        if duration > 0:
            print(f"Spent {duration}s on: {title}")
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/browser_stats", methods=["GET"])
def browser_stats():
    """Get browser usage statistics"""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        # Get browser stats from the last 24 hours
        one_day_ago = time.time() - (24 * 3600)
        c.execute("""
            SELECT app, window_title, url, COUNT(*) as visits, 
                   MAX(timestamp) as last_visit
            FROM logs 
            WHERE timestamp > ? AND app IN ('Chrome', 'Firefox')
            GROUP BY app, window_title, url
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """, (one_day_ago,))
        
        stats = []
        for row in c.fetchall():
            app, title, url, visits, last_visit = row
            stats.append({
                "app": app,
                "title": title,
                "url": url,
                "visits": visits,
                "last_visit": time.strftime("%H:%M:%S", time.localtime(last_visit))
            })
        
        conn.close()
        return jsonify({"status": "ok", "stats": stats}), 200
    except Exception as e:
        print(f"Error in browser_stats: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/app_stats", methods=["GET"])
def app_stats():
    """Get all application usage statistics (including OS apps)"""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        # Get stats from the last 24 hours for all apps
        one_day_ago = time.time() - (24 * 3600)
        c.execute("""
            SELECT app, window_title, COUNT(*) as visits, 
                   MAX(timestamp) as last_visit
            FROM logs 
            WHERE timestamp > ?
            GROUP BY app, window_title
            ORDER BY COUNT(*) DESC
            LIMIT 15
        """, (one_day_ago,))
        
        stats = []
        for row in c.fetchall():
            app, title, visits, last_visit = row
            # Handle None values for window_title
            title = title if title else "Unknown Window"
            stats.append({
                "app": app,
                "title": title,
                "visits": visits,
                "last_visit": time.strftime("%H:%M:%S", time.localtime(last_visit))
            })
        
        conn.close()
        return jsonify({"status": "ok", "stats": stats}), 200
    except Exception as e:
        print(f"Error in app_stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "running", "service": "browser_tracker"})

def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except Exception:
        return False

def _run_server_with_retries():
    while True:
        # If something is already listening, don't spawn another server.
        if _port_open("127.0.0.1", 5001):
            return
        try:
            app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
        except OSError as e:
            print(f"Browser server bind failed: {e}. Retrying...")
            time.sleep(1.5)
        except Exception as e:
            print(f"Browser server error: {e}. Retrying...")
            time.sleep(1.5)

def start_browser_server():
    threading.Thread(target=_run_server_with_retries, daemon=True).start()
