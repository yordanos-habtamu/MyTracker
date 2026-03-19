from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                   QLabel, QPushButton, QTextEdit, QTableWidget, 
                                   QTableWidgetItem, QHeaderView, QSplitter,
                                   QComboBox, QCheckBox, QGroupBox, QRadioButton,
                                   QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
import sqlite3
import time
from tracker.db import get_connection

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Activity Tracker")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header with modern styling
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                           stop:0 #3498db, stop:1 #2980b9);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        
        self.title_label = QLabel("📊 Activity Tracker Dashboard")
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Control buttons
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        self.refresh_btn.clicked.connect(self.load_data)
        
        self.widget_btn = QPushButton("🖥️ Open Widget")
        self.widget_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        self.widget_btn.clicked.connect(self.open_widget)

        self.clear_btn = QPushButton("🗑️ Clear History")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        self.clear_btn.clicked.connect(self.clear_history)
        
        self.browser_stats_btn = QPushButton("🌐 Browser Stats")
        self.browser_stats_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        self.browser_stats_btn.clicked.connect(self.show_browser_stats)
        
        self.app_stats_btn = QPushButton("💻 All Apps")
        self.app_stats_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        self.app_stats_btn.clicked.connect(self.show_app_stats)
        
        header_layout.addWidget(self.app_stats_btn)
        header_layout.addWidget(self.browser_stats_btn)
        header_layout.addWidget(self.widget_btn)
        header_layout.addWidget(self.clear_btn)
        header_layout.addWidget(self.refresh_btn)
        layout.addWidget(header_widget)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Summary
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.summary_label = QLabel("Activity Summary (Last Hour)")
        self.summary_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        left_layout.addWidget(self.summary_label)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        left_layout.addWidget(self.summary_text)
        
        # Right panel - Detailed logs
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.logs_label = QLabel("Detailed Activity Logs")
        self.logs_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        right_layout.addWidget(self.logs_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Time", "Application", "Window Title", "URL"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.table)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Auto-refresh timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(10000)  # Refresh every 10 seconds
        
        # Load initial data
        self.load_data()
    
    def open_widget(self):
        """Open the floating widget"""
        from gui.widget import ActivityWidget
        self.widget = ActivityWidget()
        self.widget.show()

    def clear_history(self):
        """Clear all activity history"""
        confirm = QMessageBox.question(
            self,
            "Clear History",
            "This will permanently delete all activity history.\n\nDo you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("DELETE FROM logs")
            conn.commit()
            conn.close()
            self.load_data()
            self.status_bar.showMessage("History cleared")
        except Exception as e:
            self.status_bar.showMessage(f"Error clearing history: {e}")
    
    def load_data(self):
        """Load and display activity data"""
        try:
            conn = get_connection()
            c = conn.cursor()
            
            # Get data from last hour
            one_hour_ago = time.time() - 3600
            c.execute("""
                SELECT timestamp, app, window_title, url 
                FROM logs 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            """, (one_hour_ago,))
            
            logs = c.fetchall()
            
            # Update table
            self.table.setRowCount(len(logs))
            for row, (timestamp, app, title, url) in enumerate(logs):
                time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
                
                self.table.setItem(row, 0, QTableWidgetItem(time_str))
                self.table.setItem(row, 1, QTableWidgetItem(app))
                self.table.setItem(row, 2, QTableWidgetItem(title))
                self.table.setItem(row, 3, QTableWidgetItem(url or ""))
            
            # Generate summary
            summary = self.generate_summary(logs)
            self.summary_text.setPlainText(summary)
            
            self.status_bar.showMessage(f"Loaded {len(logs)} records")
            conn.close()
            
        except Exception as e:
            self.status_bar.showMessage(f"Error loading data: {e}")
    
    def generate_summary(self, logs):
        """Generate activity summary from logs"""
        if not logs:
            return "No activity recorded in the last hour."
        
        # Count activities by application
        app_counts = {}
        for _, app, _, _ in logs:
            app_counts[app] = app_counts.get(app, 0) + 1
        
        # Sort by count
        sorted_apps = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)
        
        summary = f"Total activities in last hour: {len(logs)}\n\n"
        summary += "Top applications:\n"
        
        for app, count in sorted_apps[:10]:
            percentage = (count / len(logs)) * 100
            summary += f"  {app}: {count} events ({percentage:.1f}%)\n"
        
        return summary
    
    def show_browser_stats(self):
        """Show browser usage statistics"""
        try:
            import urllib.request
            import json
            
            # Use urllib instead of requests to avoid dependency issues
            req = urllib.request.Request("http://localhost:5001/browser_stats")
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
            
            if data.get("status") == "ok":
                stats = data.get("stats", [])
                if stats:
                    stats_text = "🌐 Browser Usage Statistics (Last 24 Hours):\n\n"
                    for i, stat in enumerate(stats, 1):
                        stats_text += f"{i}. {stat['title']}\n"
                        stats_text += f"   App: {stat['app']}\n"
                        stats_text += f"   Visits: {stat['visits']}\n"
                        stats_text += f"   Last Visit: {stat['last_visit']}\n\n"
                    
                    # Show in a dialog or update summary
                    self.summary_text.setPlainText(stats_text)
                    self.status_bar.showMessage(f"Showing {len(stats)} browser stats")
                else:
                    self.summary_text.setPlainText("No browser activity recorded yet.")
                    self.status_bar.showMessage("No browser stats available")
            else:
                self.status_bar.showMessage("Error fetching browser stats")
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
    
    def show_app_stats(self):
        """Show all application usage statistics (including OS apps)"""
        try:
            import urllib.request
            import json
            
            # Use urllib instead of requests to avoid dependency issues
            req = urllib.request.Request("http://localhost:5001/app_stats")
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
            
            if data.get("status") == "ok":
                stats = data.get("stats", [])
                if stats:
                    stats_text = "💻 All Application Usage Statistics (Last 24 Hours):\n\n"
                    for i, stat in enumerate(stats, 1):
                        stats_text += f"{i}. {stat['title']}\n"
                        stats_text += f"   App: {stat['app']}\n"
                        stats_text += f"   Visits: {stat['visits']}\n"
                        stats_text += f"   Last Visit: {stat['last_visit']}\n\n"
                    
                    # Show in a dialog or update summary
                    self.summary_text.setPlainText(stats_text)
                    self.status_bar.showMessage(f"Showing {len(stats)} app stats")
                else:
                    self.summary_text.setPlainText("No application activity recorded yet.")
                    self.status_bar.showMessage("No app stats available")
            else:
                self.status_bar.showMessage("Error fetching app stats")
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
