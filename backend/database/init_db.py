import sqlite3
import os
import sys

# add backend folder to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import DATABASE_PATH

os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # DROP old tables (only run once during development)
    cursor.execute("DROP TABLE IF EXISTS assets")
    cursor.execute("DROP TABLE IF EXISTS violations")

    #  ASSETS TABLE (MATCHES upload_route.py EXACTLY)
    cursor.execute("""
    CREATE TABLE assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT,
        owner TEXT,
        file_hash TEXT UNIQUE,
        fingerprint TEXT,
        cid TEXT,
        tx_hash TEXT,
        file_type TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    #  VIOLATIONS TABLE
    cursor.execute("""
    CREATE TABLE violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER,
        detected_source TEXT,
        similarity REAL,
        status TEXT DEFAULT 'UNRESOLVED',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id)
    )
    """)

    conn.commit()
    conn.close()
    print(" Database initialized successfully")

if __name__ == "__main__":
    init_db()
