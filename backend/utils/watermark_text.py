import os
import hashlib
from typing import Tuple, List

# ============================================================
# CONFIG (MAINTAINED)
# ============================================================

ZERO_WIDTH = "\u200b"
WATERMARK_PREFIX = "SmartIPGuard"
SUPPORTED_TEXT_FORMATS = [".txt", ".pdf", ".docx", ".doc"]
SIDECAR_EXTENSION = ".meta"


# ============================================================
# HELPERS
# ============================================================

def _validate_text(path: str) -> Tuple[bool, str]:
    if not os.path.exists(path):
        return False, "File not found"

    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_TEXT_FORMATS:
        return False, f"Unsupported format: {ext}"

    return True, "OK"


def _build_tag(owner: str) -> bytes:
    return f"{ZERO_WIDTH}{WATERMARK_PREFIX}|{owner}{ZERO_WIDTH}".encode("utf-8")


def _build_prefix() -> bytes:
    return f"{ZERO_WIDTH}{WATERMARK_PREFIX}|".encode("utf-8")


def _file_hash(path: str) -> str:
    """Stable content hash (rename-safe)"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


# ============================================================
# APPLY WATERMARK (SAFE + COMPATIBLE)
# ============================================================

def watermark_text(file_path: str, owner: str = "SMARTIP") -> str:
    """
    ✔ Keeps original file intact
    ✔ Creates same-content watermarked copy
    ✔ EOF watermark (best-effort)
    ✔ Sidecar hash anchor (DOCX/PDF safe)
    """

    valid, msg = _validate_text(file_path)
    if not valid:
        print(msg)
        return file_path

    base, ext = os.path.splitext(file_path)
    watermarked_path = f"{base}_wm_{owner}{ext}"

    try:
        with open(file_path, "rb") as f:
            content = f.read()

        # --- EOF watermark (works for TXT, sometimes PDF/DOC) ---
        watermarked_content = content + b"\n" + _build_tag(owner)

        with open(watermarked_path, "wb") as f:
            f.write(watermarked_content)

        # --- Sidecar (AUTHORITATIVE PROOF) ---
        content_hash = _file_hash(watermarked_path)

        with open(watermarked_path + SIDECAR_EXTENSION, "w", encoding="utf-8") as f:
            f.write(
                f"PREFIX={WATERMARK_PREFIX}\n"
                f"OWNER={owner}\n"
                f"HASH={content_hash}\n"
            )

    except Exception as e:
        print("Watermark write error:", e)
        return file_path

    return watermarked_path


# ============================================================
# VERIFY WATERMARK (RENAMING SAFE, DOCX SAFE)
# ============================================================

def verify_text_watermark(file_path: str) -> Tuple[bool, str]:
    """
    ✔ Works after rename
    ✔ Owner auto-detected
    ✔ DOCX / PDF safe
    ✔ Uses watermark if present
    ✔ Falls back to sidecar if stripped
    """

    valid, msg = _validate_text(file_path)
    if not valid:
        return False, msg

    # ---------- TRY EOF WATERMARK ----------
    try:
        with open(file_path, "rb") as f:
            content = f.read()

        prefix = _build_prefix()
        idx = content.find(prefix)

        if idx != -1:
            start = idx + len(prefix)
            end = content.find(ZERO_WIDTH.encode("utf-8"), start)

            if end != -1:
                owner = content[start:end].decode("utf-8", errors="ignore")
                return True, f"Watermark verified (Owner={owner}) ✔"

    except Exception:
        pass

    # ---------- FALLBACK: SIDECAR VERIFICATION ----------
    meta_file = file_path + SIDECAR_EXTENSION
    if not os.path.exists(meta_file):
        return False, "Watermark not found"

    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = f.read()

        owner = None
        stored_hash = None

        for line in meta.splitlines():
            if line.startswith("OWNER="):
                owner = line.split("=", 1)[1]
            if line.startswith("HASH="):
                stored_hash = line.split("=", 1)[1]

        if not owner or not stored_hash:
            return False, "Invalid watermark metadata"

        current_hash = _file_hash(file_path)
        if current_hash != stored_hash:
            return False, "File modified after watermark"

        return True, f"Watermark verified via metadata (Owner={owner}) ✔"

    except Exception:
        return False, "Watermark metadata corrupted"


# ============================================================
# BATCH HELPERS (MAINTAINED)
# ============================================================

def watermark_text_folder(paths: List[str], owner="SMARTIP") -> List[str]:
    return [watermark_text(p, owner) for p in paths]


def verify_text_folder(paths: List[str]):
    return [verify_text_watermark(p) for p in paths]
