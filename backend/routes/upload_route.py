from flask import Blueprint, request, jsonify
import os, sqlite3, json
import numpy as np
from datetime import datetime
from werkzeug.utils import secure_filename

from config import DATABASE_PATH

# ---- Core utilities ----
from utils.compute_hash import compute_sha256
from utils.storage_ipfs import upload_to_ipfs
from utils.blockchain_connector import store_on_blockchain

# ---- Fingerprint + Watermark ----
from utils.fingerprint_text import fingerprint_text
from utils.fingerprint_image import fingerprint_image
from utils.fingerprint_audio import fingerprint_audio

from utils.watermark_text import watermark_text
from utils.watermark_image import watermark_image
from utils.watermark_audio import watermark_audio

# ---- Similarity ----
from utils.similarity_engine import compute_similarity_score, is_violation

# ---- Monitoring ----
from monitoring.detector import trigger_monitoring_scan


upload_bp = Blueprint("upload_bp", __name__, url_prefix="/api")

# --------------------------------------------------
# PATHS
# --------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "ipfs", "uploaded")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_FILES = {
    "text": [".txt", ".pdf", ".doc", ".docx"],
    "image": [".jpg", ".jpeg", ".png", ".bmp"],
    "audio": [".mp3",".flac", ".wav", ".aac", ".ogg"]
}

# --------------------------------------------------
# NORMALIZE FINGERPRINT
# --------------------------------------------------
def normalize_fingerprint(fp):
    if isinstance(fp, np.ndarray):
        return fp.tolist()
    if isinstance(fp, dict):
        return {k: normalize_fingerprint(v) for k, v in fp.items()}
    if isinstance(fp, (list, tuple)):
        return [normalize_fingerprint(v) for v in fp]
    return fp

# --------------------------------------------------
# FINGERPRINT GENERATOR
# --------------------------------------------------
def generate_fingerprint(file_path, file_type):
    if file_type == "text":
        return fingerprint_text(file_path)
    if file_type == "image":
        return fingerprint_image(file_path)
    if file_type == "audio":
        return fingerprint_audio(file_path)
    return None

# --------------------------------------------------
# WATERMARK
# --------------------------------------------------
def apply_watermark(file_path, file_type, owner):
    try:
        if file_type == "text":
            return watermark_text(file_path, owner)
        if file_type == "image":
            return watermark_image(file_path, owner)
        if file_type == "audio":
            return watermark_audio(file_path, owner)
    except Exception as e:
        print("Watermark failed:", e)

    return file_path

# --------------------------------------------------
# UPLOAD API
# --------------------------------------------------
@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    owner = request.form.get("owner", "anonymous")
    file_type = request.form.get("file_type")

    if not file or not file_type:
        return jsonify({"error": "File or file_type missing"}), 400

    if file_type not in ALLOWED_FILES:
        return jsonify({"error": "Invalid file category"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    if not any(filename.lower().endswith(ext) for ext in ALLOWED_FILES[file_type]):
        return jsonify({"error": "File extension mismatch"}), 400

    # ---------------- SAVE ORIGINAL (BINARY SAFE) ----------------
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    stored_filename = f"{timestamp}_{filename}"
    original_path = os.path.join(UPLOAD_FOLDER, stored_filename)

    file.save(original_path)   #  SAFE for DOCX / PDF

    # ---------------- FINGERPRINT ORIGINAL ----------------
    raw_fp = generate_fingerprint(original_path, file_type)
    if raw_fp is None:
        return jsonify({"error": "Fingerprint generation failed"}), 500

    fingerprint = normalize_fingerprint(raw_fp)
    fingerprint_json = json.dumps(fingerprint)

    # ---------------- HASH ORIGINAL ----------------
    file_hash = compute_sha256(original_path)

    conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
    cur = conn.cursor()

    # ---------------- SIMILARITY CHECK ----------------
    cur.execute("SELECT id, fingerprint FROM assets WHERE file_type=?", (file_type,))
    for asset_id, stored_fp_json in cur.fetchall():
        try:
            stored_fp = json.loads(stored_fp_json)
        except Exception:
            continue

        similarity = compute_similarity_score(fingerprint, stored_fp, file_type)

        if is_violation(similarity, file_type):
            cur.execute("""
                INSERT INTO violations (asset_id, detected_source, similarity)
                VALUES (?, ?, ?)
            """, (asset_id, stored_filename, similarity))
            conn.commit()
            conn.close()

            return jsonify({
                "violation": True,
                "file_type": file_type,
                "similarity": similarity
            }), 409

    # ---------------- WATERMARK (SAFE MODES) ----------------
    watermarked_path = original_path

    try:
        if file_type == "text":
            watermarked_path = watermark_text(original_path, owner)

        elif file_type == "image":
            watermarked_path = watermark_image(original_path, owner)

        elif file_type == "audio":
            watermarked_path = watermark_audio(original_path, owner)

        #  DO NOT watermark DOCX / PDF as text
        # These should use metadata-based watermarking later

    except Exception as e:
        print(" Watermark skipped:", e)
        watermarked_path = original_path

    # ---------------- IPFS ----------------
    try:
        cid = upload_to_ipfs(watermarked_path)
    except Exception:
        cid = "IPFS_UNAVAILABLE"

    # ---------------- BLOCKCHAIN ----------------
    try:
        tx_hash = store_on_blockchain(file_hash, cid, owner)
    except Exception:
        tx_hash = "BLOCKCHAIN_UNAVAILABLE"

    # ---------------- STORE ASSET ----------------
    cur.execute("""
        INSERT INTO assets
        (file_name, owner, file_hash, fingerprint, cid, tx_hash, file_type, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        stored_filename,
        owner,
        file_hash,
        fingerprint_json,
        cid,
        tx_hash,
        file_type,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    # ---------------- MONITORING ----------------
    trigger_monitoring_scan({
        "file_hash": file_hash,
        "fingerprint": fingerprint,
        "file_type": file_type,
        "owner": owner
    })

    return jsonify({
        "success": True,
        "file_hash": file_hash,
        "cid": cid,
        "tx_hash": tx_hash
    }), 201

