import os
import json
import sqlite3
import numpy as np
from datetime import datetime

from config import DATABASE_PATH
from utils.fingerprinting import generate_fingerprint
from utils.similarity_engine import compute_similarity_score, is_violation


# -------- LEGACY HELPER --------

def extract_downloaded_file(source_path):
    if os.path.exists(source_path):
        return source_path
    return None


# -------- FILE TYPE DETECTION --------

def detect_file_type(filename):
    ext = os.path.splitext(filename.lower())[1]

    if ext in [".txt", ".pdf", ".doc", ".docx"]:
        return "text"
    if ext in [".jpg", ".jpeg", ".png", ".bmp"]:
        return "image"
    if ext in [".mp3", ".wav", ".aac", ".ogg"]:
        return "audio"
    return None


# -------- WAL ENABLER --------

def _enable_wal(conn):
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")


# -------- DETECTOR --------

def trigger_monitoring_scan(
    crawled_files=None,
    fingerprint=None,
    file_type=None,
    source="VERIFY"
):

    # ✔ use timeout + WAL + busy retry
    with sqlite3.connect(DATABASE_PATH, timeout=20) as conn:
        cur = conn.cursor()
        _enable_wal(conn)

        if fingerprint and file_type:
            cur.execute("""
                SELECT id, fingerprint
                FROM assets
                WHERE file_type=?
            """, (file_type,))

            for asset_id, asset_fp_json in cur.fetchall():
                asset_fp = json.loads(asset_fp_json)

                similarity = compute_similarity_score(
                    fingerprint,
                    asset_fp,
                    file_type
                )

                # ✔ write using SAME connection
                if is_violation(similarity, file_type):
                    cur.execute("""
                        INSERT INTO violations
                        (asset_id, detected_source, similarity, timestamp, status)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        asset_id,
                        source,
                        round(similarity, 2),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "CONFIRMED"
                    ))

            conn.commit()
            return

        # ✔ crawler mode
        if not crawled_files:
            return

        cur.execute("SELECT id, file_type, fingerprint FROM assets")
        assets = cur.fetchall()

        for file_path in crawled_files:
            detected_type = detect_file_type(file_path)
            if not detected_type:
                continue

            crawled_fp = generate_fingerprint(file_path, detected_type)

            for asset_id, asset_type, asset_fp_json in assets:
                if asset_type != detected_type:
                    continue

                asset_fp = json.loads(asset_fp_json)

                similarity = compute_similarity_score(
                    crawled_fp,
                    asset_fp,
                    detected_type
                )

                if is_violation(similarity, detected_type):
                    cur.execute("""
                        INSERT INTO violations
                        (asset_id, detected_source, similarity, timestamp, status)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        asset_id,
                        file_path,
                        round(similarity, 2),
                        datetime.utcnow().isoformat(),
                        "DETECTED"
                    ))

        conn.commit()
