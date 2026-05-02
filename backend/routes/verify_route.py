from flask import Blueprint, request, jsonify
import os
import sqlite3
import json

from config import DATABASE_PATH

from utils.fingerprint_text import fingerprint_text
from utils.fingerprint_image import fingerprint_image
from utils.fingerprint_audio import fingerprint_audio
from utils.similarity_engine import compute_similarity_score

from utils.watermark_text import verify_text_watermark
from utils.watermark_image import verify_image_watermark
from utils.watermark_audio import verify_audio_watermark

from monitoring.detector import trigger_monitoring_scan


verify_bp = Blueprint("verify_bp", __name__, url_prefix="/api")

TEMP_VERIFY_FOLDER = os.path.join("ipfs", "verify_tmp")
os.makedirs(TEMP_VERIFY_FOLDER, exist_ok=True)

# --------------------------------------------------
# THRESHOLDS (UNCHANGED)
# --------------------------------------------------

THRESHOLDS = {
    "text": 70,
    "image": 75,
    "audio": 65
}

FILE_FORMATS = {
    "text":  [".txt", ".pdf", ".doc", ".docx"],
    "image": [".jpg", ".jpeg", ".png", ".bmp"],
    "audio": [".wav", ".flac", ".mp3", ".aac", ".ogg"]
}

# --------------------------------------------------
# UTILS
# --------------------------------------------------

def detect_file_type(filename):
    ext = os.path.splitext(filename.lower())[1]
    for ftype, extensions in FILE_FORMATS.items():
        if ext in extensions:
            return ftype
    return None


def generate_fingerprint(file_path, file_type):
    if file_type == "text":
        return fingerprint_text(file_path)
    if file_type == "image":
        return fingerprint_image(file_path)
    if file_type == "audio":
        return fingerprint_audio(file_path)
    return None


# ==================================================
# ✔ WATERMARK VERIFICATION
# ==================================================

def verify_watermark(file_path, file_type) -> bool:
    try:
        if file_type == "text":
            ok, _ = verify_text_watermark(file_path)
            return ok

        if file_type == "image":
            ok, _ = verify_image_watermark(file_path)
            return ok

        if file_type == "audio":
            ok, _ = verify_audio_watermark(file_path)
            return ok

    except Exception as e:
        print("Watermark verification error:", e)

    return False


# ==================================================
# API
# ==================================================

@verify_bp.route("/verify", methods=["POST"])
def verify_file():

    file = request.files.get("file")
    owner = request.form.get("owner", "unknown")

    if not file:
        return jsonify({"error": "File missing"}), 400

    file_type = detect_file_type(file.filename)
    if not file_type:
        return jsonify({"error": "Unsupported file type"}), 400

    temp_path = os.path.join(TEMP_VERIFY_FOLDER, file.filename)
    file.save(temp_path)

    # ---------------- ANALYSIS ----------------

    fingerprint = generate_fingerprint(temp_path, file_type)
    watermark_found = verify_watermark(temp_path, file_type)

    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, file_name, owner, fingerprint
        FROM assets
        WHERE file_type=?
    """, (file_type,))
    assets = cur.fetchall()

    best_match = None
    best_similarity = 0.0

    for asset_id, file_name, asset_owner, stored_fp_json in assets:
        try:
            stored_fp = json.loads(stored_fp_json)
        except:
            continue

        similarity = compute_similarity_score(
            fingerprint,
            stored_fp,
            file_type
        )

        if similarity > best_similarity:
            best_similarity = similarity
            best_match = (asset_id, file_name, asset_owner)

    # ==================================================
    # ✔ FINAL DECISION LOGIC
    # ==================================================

    violation = False
    status = "Verified Original"

    if watermark_found and best_similarity < THRESHOLDS[file_type]:
        status = "Watermark Detected – No Infringement"

    if best_similarity >= 90:
        violation = True
        status = "Confirmed Infringement"

    elif best_similarity >= THRESHOLDS[file_type]:
        violation = True
        status = "High Similarity Detected"

    elif best_similarity >= 40:
        status = "Partial Similarity"

    # ---------------- MONITORING ----------------

    if violation:
        trigger_monitoring_scan(
            fingerprint=fingerprint,
            file_type=file_type,
            source="VERIFY"
        )

    conn.close()

    try:
        os.remove(temp_path)
    except:
        pass

    return jsonify({
        "verified": not violation,
        "status": status,
        "similarity_score": round(best_similarity, 2),
        "matched_file": best_match[1] if best_match else "N/A",
        "owner": best_match[2] if best_match else "N/A",
        "watermark_detected": watermark_found,
        "violation_logged": violation
    })
