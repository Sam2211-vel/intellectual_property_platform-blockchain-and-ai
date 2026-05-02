from flask import Blueprint, jsonify
import sqlite3
from config import DATABASE_PATH

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard", methods=["GET"])
def get_dashboard_data():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT file_name, owner, file_hash, cid, tx_hash, timestamp
        FROM assets
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    conn.close()

    assets = [{
        "file_name": r[0],
        "owner": r[1],
        "file_hash": r[2],
        "cid": r[3],
        "tx_hash": r[4],
        "timestamp": r[5]
    } for r in rows]

    return jsonify({"assets": assets})
