from flask import Blueprint, jsonify
import sqlite3
from datetime import datetime, timezone
from config import DATABASE_PATH

alerts_bp = Blueprint("alerts_bp", __name__, url_prefix="/api")

# --------------------------------------------------
# GET ALL VIOLATION ALERTS
# --------------------------------------------------
@alerts_bp.route("/alerts", methods=["GET"])
def get_alerts():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            a.file_name,
            a.owner,
            v.detected_source,
            v.similarity,
            v.timestamp
        FROM violations v
        JOIN assets a ON v.asset_id = a.id
        ORDER BY v.timestamp DESC
    """)

    rows = cur.fetchall()
    conn.close()

    violations = []

    for r in rows:
        raw_ts = r[4]

        # ---- TIMESTAMP NORMALIZATION ----
        try:
            dt = datetime.fromisoformat(raw_ts)
        except Exception:
            dt = datetime.fromtimestamp(float(raw_ts))

        dt_utc = dt.replace(tzinfo=timezone.utc)

        similarity = r[3]

        # ---- AUTO STATUS (ML BASED) ----
        if similarity >= 90:
            status = "Confirmed Infringement"
        elif similarity >= 50:
            status = "Partial Similarity"
        else:
            status = "Suspicious / Unknown Source"

        violations.append({
            "original_file": r[0],
            "owner": r[1],
            "matched_source": r[2],
            "similarity": similarity,
            "status": status,
            "date": dt_utc.isoformat()
        })

    return jsonify({
        "count": len(violations),
        "violations": violations
    })


# --------------------------------------------------
# CLEAR ALL ALERTS
# --------------------------------------------------
@alerts_bp.route("/alerts/clear", methods=["DELETE"])
def clear_alerts():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    cur.execute("DELETE FROM violations")
    conn.commit()
    conn.close()

    return jsonify({
        "message": "All violation alerts cleared successfully"
    })