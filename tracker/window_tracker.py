import time
import threading
import psutil
import platform
from .db import get_connection

def get_active_window():
    system = platform.system()
    if system == "Windows":
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        pid = win32gui.GetWindowThreadProcessId(hwnd)[1]
        try:
            app = psutil.Process(pid).name()
            # For better window identification, use window class name
            class_name = win32gui.GetClassName(hwnd)
            if title:
                window_id = f"{app} - {title}"
            else:
                window_id = f"{app} - {class_name}"
        except:
            window_id = "Unknown Window"
            app = "Unknown"
    elif system == "Darwin":  # macOS
        import subprocess
        try:
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set frontAppTitle to name of first window of application process frontApp
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            app, title = result.stdout.strip().split('\n')
            if title:
                window_id = f"{app} - {title}"
            else:
                window_id = app
        except:
            window_id = "Unknown Window"
            app = "Unknown"
    elif system == "Linux":
        import subprocess
        try:
            # Get window title
            result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'], 
                                  capture_output=True, text=True)
            title = result.stdout.strip()
            
            # Get process name from window ID
            result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowpid'], 
                                  capture_output=True, text=True)
            pid = int(result.stdout.strip())
            app = psutil.Process(pid).name()
            
            if title:
                window_id = f"{app} - {title}"
            else:
                window_id = app
        except:
            window_id = "Unknown Window"
            app = "Unknown"
    else:
        window_id = "Unknown Window"
        app = "Unknown"
    
    return app, window_id

def tracker_loop():
    conn = get_connection()
    c = conn.cursor()
    
    # Track window changes to calculate duration
    last_window = None
    window_start_time = time.time()
    
    while True:
        try:
            app, window_id = get_active_window()
            
            # Check if window changed
            current_time = time.time()
            if last_window is not None and window_id != last_window:
                # Calculate duration for previous window
                duration = current_time - window_start_time
                
                # Only log if duration is significant (more than 1 second)
                if duration > 1.0:
                    c.execute("INSERT INTO logs VALUES (?, ?, ?, ?)", 
                             (window_start_time, app, window_id, None))
                    conn.commit()
            
            # Update tracking variables
            if window_id != last_window:
                window_start_time = current_time
                last_window = window_id
            
        except Exception as e:
            print(f"Error tracking window: {e}")
        
        time.sleep(5)

def start_os_tracker():
    threading.Thread(target=tracker_loop, daemon=True).start()
