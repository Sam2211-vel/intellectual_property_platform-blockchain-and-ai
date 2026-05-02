import os
import sys
import warnings
import sqlite3
import json
from datetime import datetime

# ================================================================
# TF / KERAS SILENCE (SAFE)
# ================================================================
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import tensorflow as tf
tf.get_logger().setLevel("ERROR")
tf.autograph.set_verbosity(0)

# --------------------------------------------------
# FIX PYTHON PATH
# --------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

# --------------------------------------------------
# IMPORTS
# --------------------------------------------------
from config import DATABASE_PATH
from utils.fingerprinting import generate_fingerprint
from utils.similarity_engine import compute_similarity, is_violation
from monitoring.crawler import crawl_web_sources
from monitoring.detector import extract_downloaded_file, detect_file_type

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
MONITOR_LOG = "[MONITORING]"

# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------
def run_monitoring():
    print(f"{MONITOR_LOG} Monitoring started...")

    conn = sqlite3.connect(DATABASE_PATH, timeout=20)
    cur = conn.cursor()

    # 1️⃣ Load registered assets WITH fingerprints
    cur.execute("""
        SELECT id, file_name, file_type, fingerprint
        FROM assets
    """)
    assets = cur.fetchall()

    if not assets:
        print(f"{MONITOR_LOG} No registered assets found.")
        conn.close()
        return

    # 2️⃣ Crawl web (simulated)
    suspicious_sources = crawl_web_sources()

    if not suspicious_sources:
        print(f"{MONITOR_LOG} No suspicious sources detected.")
        conn.close()
        return

    # 3️⃣ Analyze sources
    for source in suspicious_sources:
        try:
            downloaded_file = extract_downloaded_file(source)
            if not downloaded_file:
                continue

            detected_type = detect_file_type(downloaded_file)
            if not detected_type:
                continue

            # ✔ Generate fingerprint for suspect file
            suspect_fp = generate_fingerprint(downloaded_file, detected_type)

            for asset_id, asset_name, asset_type, asset_fp_json in assets:
                if asset_type != detected_type:
                    continue

                asset_fp = json.loads(asset_fp_json)

                similarity = compute_similarity(
                    suspect_fp,
                    asset_fp,
                    asset_type
                )

                if is_violation(similarity, asset_type):
                    print(
                        f"{MONITOR_LOG} Violation detected | "
                        f"{asset_name} | {similarity}%"
                    )

                    cur.execute("""
                        INSERT INTO violations
                        (asset_id, detected_source, similarity, status, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        asset_id,
                        source,
                        round(similarity, 2),
                        "AUTO_DETECTED",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))

            conn.commit()

        except Exception as e:
            print(f"{MONITOR_LOG} Error processing:", source)
            print(e)

    conn.close()
    print(f"{MONITOR_LOG} Monitoring completed successfully.")


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------
if __name__ == "__main__":
    run_monitoring()
