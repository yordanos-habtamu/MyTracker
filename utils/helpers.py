import time
import platform
import subprocess
import psutil
from pathlib import Path

def get_system_info():
    """Get system information for debugging"""
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": platform.python_version(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor()
    }

def format_duration(seconds):
    """Format duration in seconds to human-readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def get_active_window_info():
    """Get current active window information"""
    try:
        system = platform.system()
        if system == "Windows":
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            pid = win32gui.GetWindowThreadProcessId(hwnd)[1]
            app = psutil.Process(pid).name()
        elif system == "Darwin":  # macOS
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set frontAppTitle to name of first window of application process frontApp
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            app, title = result.stdout.strip().split('\n')
        elif system == "Linux":
            # Get window title
            result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'], 
                                  capture_output=True, text=True)
            title = result.stdout.strip()
            # Get process name
            result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowpid'], 
                                  capture_output=True, text=True)
            pid = int(result.stdout.strip())
            app = psutil.Process(pid).name()
        else:
            app, title = "Unknown", "Unknown"
        
        return app, title
    except Exception as e:
        return "Error", str(e)

def is_port_in_use(port):
    """Check if a port is in use"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_db_size():
    """Get the size of the activity database"""
    db_path = Path(__file__).parent.parent / "activity.db"
    if db_path.exists():
        return db_path.stat().st_size
    return 0

def cleanup_old_logs(days=7):
    """Clean up logs older than specified days"""
    import sqlite3
    from tracker.db import get_connection
    
    try:
        conn = get_connection()
        c = conn.cursor()
        cutoff_time = time.time() - (days * 24 * 3600)
        c.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff_time,))
        deleted_count = c.rowcount
        conn.commit()
        conn.close()
        return deleted_count
    except Exception as e:
        print(f"Error cleaning up logs: {e}")
        return 0