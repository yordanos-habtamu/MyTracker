import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent.parent / "activity.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            timestamp REAL,
            app TEXT,
            window_title TEXT,
            url TEXT
        )
    """)
    conn.commit()
    conn.close()
