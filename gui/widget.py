import math
import os
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, QTimer, QProcess
from PyQt6.QtGui import QFont, QColor, QPainter, QPen

try:
    from tracker.db import get_connection
except ImportError:
    get_connection = None

class ActivityWidget(QWidget):
    def __init__(self, desktop_mode: bool = True):
        super().__init__()
        self.desktop_mode = desktop_mode
        # Compact, flat dimensions
        self.setFixedSize(280, 560) 
        
        flags = (Qt.WindowType.FramelessWindowHint | 
                 Qt.WindowType.WindowStaysOnBottomHint | 
                 Qt.WindowType.Tool |
                 Qt.WindowType.SubWindow |
                 Qt.WindowType.Desktop)
        
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        if self.desktop_mode:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # Flat Palette: Pure Amber on Deep Charcoal
        self.clr_amber = QColor(255, 140, 0)
        self.clr_bg = QColor(10, 10, 10, 235) 
        
        self.tick = 0
        self._stats_data = [] 
        self._history_data = [0] * 24
        self._gui_launch_cooldown_until = 0
        
        self.init_ui()
        self._position_on_right()
        
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._update_animations)
        self.anim_timer.start(50) 

        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.refresh_telemetry)
        self.data_timer.start(5000) 
        
        self.refresh_telemetry()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 25, 15, 25)
        layout.setSpacing(10)

        # DNA HELIX (Visual Centerpiece)
        self.helix_lbl = QLabel()
        self.helix_lbl.setFont(QFont("Monospace", 9, QFont.Weight.Bold))
        self.helix_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.helix_lbl.setStyleSheet(f"color: {self.clr_amber.name()};")
        layout.addWidget(self.helix_lbl)

        layout.addWidget(self._make_flat_sep("LIVE_LOG"))

        # TELEMETRY BARS
        self.stats_lbl = QLabel("...")
        self.stats_lbl.setFont(QFont("Monospace", 8))
        self.stats_lbl.setStyleSheet(f"color: {self.clr_amber.name()};")
        layout.addWidget(self.stats_lbl)

        layout.addStretch()

        # CHRONO-GRAPH (24H Activity Histogram)
        layout.addWidget(self._make_flat_sep("24H_ACT"))
        self.graph_lbl = QLabel()
        self.graph_lbl.setFont(QFont("Monospace", 7))
        self.graph_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graph_lbl.setStyleSheet(f"color: {self.clr_amber.name()};")
        layout.addWidget(self.graph_lbl)

        # FOOTER (System Status)
        self.status_footer = QLabel(f"NODE_{random.randint(10,99)}")
        self.status_footer.setFont(QFont("Monospace", 7))
        self.status_footer.setStyleSheet("color: rgba(255, 140, 0, 120);")
        layout.addWidget(self.status_footer)

    def _make_flat_sep(self, text):
        lbl = QLabel(f"[{text}]" + "-" * (18 - len(text)))
        lbl.setFont(QFont("Monospace", 7, QFont.Weight.Bold))
        lbl.setStyleSheet("color: rgba(255, 140, 0, 130);")
        return lbl

    def _generate_dna(self):
        # Sparse rows for the 3D trick
        rows, width, speed = 14, 16, 0.15 
        lines = []
        for i in range(rows):
            angle = (self.tick * speed) + (i * 0.45)
            x1 = int(math.sin(angle) * (width/2) + (width/2))
            x2 = int(math.sin(angle + math.pi) * (width/2) + (width/2))
            z = math.cos(angle)
            line = [" "] * (width + 1)
            
            if i % 4 == 0:
                s, e = min(x1, x2), max(x1, x2)
                if e-s > 3:
                    for j in range(s+1, e): line[j] = "-"
            
            # Shading: '8' for front, '.' for back
            line[x1] = "8" if z > 0 else "."
            line[x2] = "8" if z < 0 else "."
            lines.append("".join(line))
        return "\n".join(lines)

    def _generate_history_graph(self):
        max_h = max(self._history_data) if max(self._history_data) > 0 else 1
        graph = []
        for i in range(0, 24, 2):
            val = (self._history_data[i] + self._history_data[i+1]) / 2
            bar_h = int((val / max_h) * 4)
            chars = [" ", " ", "▂", "▃", "▄", "▅"]
            graph.append(chars[min(bar_h, 5)])
        return " ".join(graph)

    def _update_animations(self):
        self.tick += 1
        self.helix_lbl.setText(self._generate_dna())
        if self.tick % 20 == 0:
            self.graph_lbl.setText(self._generate_history_graph())
        self.update()

    def _position_on_right(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width(), (screen.height() - self.height()) // 2)

    def refresh_telemetry(self):
        if not get_connection: return
        try:
            conn = get_connection()
            c = conn.cursor()
            # Top 4 Apps
            c.execute("SELECT app, window_title, COUNT(*) FROM logs WHERE timestamp > ? GROUP BY app, window_title ORDER BY 3 DESC LIMIT 4", (time.time() - 3600,))
            self._stats_data = c.fetchall()
            
            # Historical 24h Data
            self._history_data = []
            now = time.time()
            for h in range(24):
                start = now - ((h+1) * 3600)
                end = now - (h * 3600)
                c.execute("SELECT COUNT(*) FROM logs WHERE timestamp BETWEEN ? AND ?", (start, end))
                self._history_data.insert(0, c.fetchone()[0])

            c.execute("SELECT app, window_title, timestamp FROM logs ORDER BY timestamp DESC LIMIT 1")
            last_row = c.fetchone()
            conn.close()
            
            self._update_stats_display()
            if last_row:
                app, title, ts = last_row
                stamp = time.strftime("%H:%M", time.localtime(ts))
                active = f"{app.split('/')[-1]}: {title or '...'}"
                self.status_footer.setText(f"LNK {stamp} > {active[:18]}")
        except: pass

    def _update_stats_display(self):
        if not self._stats_data: return
        max_val = max(row[2] for row in self._stats_data)
        output = []
        for app, title, count in self._stats_data:
            name = f"{app.split('/')[-1][:8]}: {title[:12]}"
            fill = int((count/max_val) * 10) if max_val else 0
            bar = "█" * fill + " " * (10 - fill)
            output.append(f"{name}\n[{bar}]")
        self.stats_lbl.setText("\n".join(output))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.clr_bg)
        # Left flat accent line
        painter.setPen(QPen(self.clr_amber, 2))
        painter.drawLine(0, 0, 0, self.height())

    def mousePressEvent(self, event):
        if self.desktop_mode and event.button() == Qt.MouseButton.LeftButton:
            now = time.time()
            if now > self._gui_launch_cooldown_until:
                self._gui_launch_cooldown_until = now + 1.0
                self._launch_gui()

    def _launch_gui(self):
        try:
            repo_root = Path(__file__).resolve().parents[1]
            # Prefer QProcess for GUI launches; fall back to subprocess if needed.
            started = QProcess.startDetached(sys.executable, ["main.py", "--gui"], str(repo_root))
            if not started:
                subprocess.Popen([sys.executable, "main.py", "--gui"], cwd=str(repo_root))
        except: pass

    def showEvent(self, event):
        super().showEvent(event)
        self._pin_to_desktop()

    def _pin_to_desktop(self):
        if os.environ.get("XDG_SESSION_TYPE") == "x11":
            try:
                win_id = hex(int(self.winId()))
                subprocess.run(["xprop", "-id", win_id, "-f", "_NET_WM_WINDOW_TYPE", "32a", "-set", "_NET_WM_WINDOW_TYPE", "_NET_WM_WINDOW_TYPE_DESKTOP"], capture_output=True)
                subprocess.run(["xprop", "-id", win_id, "-f", "_NET_WM_STATE", "32a", "-set", "_NET_WM_STATE", "_NET_WM_STATE_BELOW"], capture_output=True)
            except: pass
