from tracker.db import init_db
from tracker.window_tracker import start_os_tracker
from tracker.browser_tracker import start_browser_server
from PyQt6.QtWidgets import QApplication
from gui.widget import ActivityWidget
from gui.main_window import MainWindow
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Activity Tracker')
    parser.add_argument('--gui', action='store_true', help='Open main GUI window')
    parser.add_argument('--widget', action='store_true', help='Open floating widget')
    parser.add_argument('--desktop-widget', action='store_true', help='Open non-interactive desktop widget (Conky-style)')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    # Start tracking services
    start_os_tracker()
    start_browser_server()
    
    # Start GUI if requested
    if args.gui or args.widget or args.desktop_widget or args.test:
        app = QApplication(sys.argv)
        # Keep background trackers running when the last window/widget is closed
        app.setQuitOnLastWindowClosed(False)
        
        if args.gui:
            window = MainWindow()
            window.show()
        elif args.widget:
            widget = ActivityWidget()
            widget.show()
        elif args.desktop_widget:
            widget = ActivityWidget(desktop_mode=True)
            widget.show()
        elif args.test:
            # Test mode - show both
            window = MainWindow()
            window.show()
            widget = ActivityWidget()
            widget.show()
        
        sys.exit(app.exec())
    else:
        print("Activity Tracker started in background mode.")
        print("Use --gui to open the main window, --widget for the floating widget, or --test for both.")
        # Keep the script running
        import time
        while True:
            time.sleep(60)

if __name__ == "__main__":
    main()
