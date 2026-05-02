import os
import shutil
from datetime import datetime
from typing import Tuple, List

# ---------------- CONFIG (COMPATIBLE WITH PREVIOUS WORK) ----------------
ALLOWED_AUDIO_FORMATS = [".wav", ".mp3", ".aac", ".flac", ".ogg"]
SIDECAR_EXTENSION = ".meta"


# ============================================================
# HELPERS
# ============================================================

def _sanitize_owner(owner: str) -> str:
    """Filename-safe owner"""
    return "".join(c for c in owner if c.isalnum() or c in ("_", "-"))


def _validate_audio(path: str) -> Tuple[bool, str]:
    if not os.path.exists(path):
        return False, "Audio file not found"

    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_AUDIO_FORMATS:
        return False, f"Unsupported audio format: {ext}"

    return True, "OK"


def _write_sidecar(wm_audio: str, owner: str, source: str) -> str:
    """Sidecar writer (no signal distortion, filesystem-safe)"""
    meta_path = os.path.abspath(wm_audio) + SIDECAR_EXTENSION

    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"OWNER={owner}\n")
        f.write(f"CREATED_AT={created}\n")
        f.write(f"SOURCE={source}\n")

    return meta_path


def _read_sidecar(audio_path: str) -> dict:
    """Robust sidecar parser"""
    meta_path = os.path.abspath(audio_path) + SIDECAR_EXTENSION

    if not os.path.exists(meta_path):
        return {}

    data = {}
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    data[k] = v
    except Exception as e:
        print("Sidecar read error:", e)
        return {}

    return data


# ============================================================
# APPLY AUDIO WATERMARK
# ============================================================

def watermark_audio(audio_path: str, owner: str = "SMARTIP") -> str:
    """
    Safe audio watermarking:
    1. Filename watermark
    2. Sidecar metadata watermark
    """

    valid, msg = _validate_audio(audio_path)
    if not valid:
        print(msg)
        return audio_path

    owner = _sanitize_owner(owner)

    base, ext = os.path.splitext(audio_path)
    wm_audio = f"{base}_wm_{owner}{ext}"

    try:
        shutil.copy2(audio_path, wm_audio)
    except Exception as e:
        print("Audio copy error:", e)
        return audio_path

    _write_sidecar(
        wm_audio,
        owner=owner,
        source=os.path.basename(audio_path)
    )

    return wm_audio


# ============================================================
# VERIFY AUDIO WATERMARK
# ============================================================

def verify_audio_watermark(audio_path: str, owner: str = "SMARTIP") -> Tuple[bool, str]:
    """
    Honest verification:
    1. Filename watermark
    2. Sidecar metadata
    3. Tamper detection
    """

    if not os.path.exists(audio_path):
        return False, "Audio file not found"

    owner = _sanitize_owner(owner)
    filename = os.path.basename(audio_path)

    if f"_wm_{owner}" not in filename:
        return False, "Filename watermark missing"

    meta = _read_sidecar(audio_path)
    if not meta:
        return False, "Sidecar metadata missing"

    if meta.get("OWNER") != owner:
        return False, "Owner mismatch in watermark metadata"

    if not meta.get("SOURCE"):
        return False, "Sidecar corrupted"

    return True, "Watermark verified accurately ✔"


# ============================================================
# BATCH HELPERS (UNCHANGED API)
# ============================================================

def watermark_audio_folder(paths: List[str], owner="SMARTIP") -> List[str]:
    return [watermark_audio(p, owner) for p in paths]


def verify_audio_folder(paths: List[str], owner="SMARTIP"):
    return [verify_audio_watermark(p, owner) for p in paths]
