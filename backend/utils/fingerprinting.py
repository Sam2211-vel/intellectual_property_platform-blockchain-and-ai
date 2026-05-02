import os

from utils.fingerprint_text import fingerprint_text
from utils.fingerprint_image import fingerprint_image
from utils.fingerprint_audio import fingerprint_audio
from utils.compute_hash import compute_sha256


def generate_fingerprint(file_path: str, file_type: str):
    """
    Unified fingerprint generator for all asset types

    Args:
        file_path (str): path to uploaded file
        file_type (str): text | image | audio

    Returns:
        dict: fingerprint data
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError("File not found for fingerprinting")

    file_type = file_type.lower()

    # --------------------------------------------------
    # TEXT FILES
    # --------------------------------------------------
    if file_type == "text":
        text_fp = fingerprint_text(file_path)

        return {
            "type": "text",
            "fingerprint": text_fp,
            "hash": compute_sha256(file_path)
        }

    # --------------------------------------------------
    # IMAGE FILES
    # --------------------------------------------------
    elif file_type == "image":
        image_fp = fingerprint_image(file_path)

        return {
            "type": "image",
            "fingerprint": image_fp,
            "hash": compute_sha256(file_path)
        }

    # --------------------------------------------------
    # AUDIO FILES
    # --------------------------------------------------
    elif file_type == "audio":
        audio_fp = fingerprint_audio(file_path)

        return {
            "type": "audio",
            "fingerprint": audio_fp,
            "hash": compute_sha256(file_path)
        }

    # --------------------------------------------------
    # FALLBACK (UNKNOWN FILE TYPE)
    # --------------------------------------------------
    else:
        # Fallback: hash-only fingerprint
        return {
            "type": "unknown",
            "fingerprint": None,
            "hash": compute_sha256(file_path)
        }
