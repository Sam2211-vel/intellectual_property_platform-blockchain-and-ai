import os
from PIL import Image, ImageDraw, PngImagePlugin
import hashlib
from typing import Tuple


# ---------------- CONFIG (COMPATIBLE) ----------------
ALLOWED_FORMATS = [".png", ".jpg", ".jpeg", ".bmp"]
DEFAULT_WM_POS = (10, 10)
VISIBLE_FILL = (255, 255, 255)


# ---------------- HELPER ----------------
def _image_pixel_hash(image: Image.Image) -> str:
    """
    Hash image pixel data (robust against metadata changes)
    """
    return hashlib.sha256(image.tobytes()).hexdigest()


def _validate_image_path(image_path: str) -> Tuple[bool, str]:
    if not os.path.exists(image_path):
        return False, "Image file not found"

    ext = os.path.splitext(image_path)[1].lower()
    if ext not in ALLOWED_FORMATS:
        return False, f"Unsupported format: {ext}"

    return True, "OK"


# ---------------- APPLY WATERMARK ----------------
def watermark_image(
    image_path: str,
    owner: str,
    watermark_prefix: str = "SmartIPGuard"
) -> str:
    """
    Create robust watermark:
    1. Visible layer
    2. Metadata layer
    3. Pixel-based tamper hash
    """

    valid, msg = _validate_image_path(image_path)
    if not valid:
        print(msg)
        base, _ = os.path.splitext(image_path)
        return base + "_watermarked.png"

    # -------- LOAD IMAGE --------
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    watermark_text = f"{watermark_prefix} | Owner: {owner}"

    # -------- VISIBLE LAYER --------
    draw.text(DEFAULT_WM_POS, watermark_text, fill=VISIBLE_FILL)

    # -------- COMPUTE HASH AFTER WATERMARK --------
    pixel_hash = _image_pixel_hash(image)

    # -------- OUTPUT PATH (SAFE) --------
    base, _ = os.path.splitext(image_path)
    output_path = base + "_watermarked.png"  # force PNG (metadata-safe)

    # -------- METADATA LAYER --------
    try:
        meta = PngImagePlugin.PngInfo()
        meta.add_text("smartipguard_watermark", watermark_text)
        meta.add_text("smartipguard_pixel_hash", pixel_hash)

        image.save(output_path, pnginfo=meta, format="PNG")

    except Exception as e:
        print("Watermark save error:", e)
        image.save(output_path, format="PNG")

    return output_path


# ---------------- VERIFY WATERMARK ----------------
def verify_image_watermark(image_path: str) -> Tuple[bool, str]:
    """
    Accurate verification:
    - Metadata watermark
    - Prefix validation
    - Pixel-level tamper detection
    """

    if not os.path.exists(image_path):
        return False, "Image file not found"

    try:
        image = Image.open(image_path).convert("RGB")

        # -------- METADATA CHECK --------
        wm_meta = image.info.get("smartipguard_watermark")
        if not wm_meta:
            return False, "Watermark metadata missing"

        # -------- PREFIX VALIDATION --------
        if "SmartIPGuard" not in wm_meta:
            return False, "Watermark prefix invalid"

        # -------- TAMPER DETECTION --------
        stored_hash = image.info.get("smartipguard_pixel_hash")
        if not stored_hash:
            return False, "Integrity hash missing"

        current_hash = _image_pixel_hash(image)
        if current_hash != stored_hash:
            return False, "Image modified after watermark"

        return True, "Watermark verified accurately ✔"

    except Exception:
        return False, "Invalid or corrupted image"


# ---------- BATCH HELPERS (MAINTAINED) ----------
def watermark_image_folder(paths, owner):
    return [watermark_image(p, owner) for p in paths]


def verify_image_folder(paths):
    return [verify_image_watermark(p) for p in paths]
