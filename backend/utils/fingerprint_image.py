import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from PIL import Image
import imagehash
import hashlib
import numpy as np
import cv2

# ================= CNN IMPORTS =================
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array

# ================= LOAD CNN ONCE =================
_CNN_MODEL = MobileNetV2(
    weights="imagenet",
    include_top=False,
    pooling="avg",
    input_shape=(224, 224, 3)
)

CNN_INPUT_SIZE = (224, 224)


def fingerprint_image(image_path: str):
    """
    SAFE Image Fingerprint
    ✔ Hash → originality
    ✔ Traditional → infringement
    ✔ CNN → visual similarity ONLY
    """

    if not os.path.exists(image_path):
        return {
            "hash": None,
            "vector": [],
            "matrix": [],
            "cnn_vector": []
        }

    # ---------------- LOAD IMAGE ----------------
    image = Image.open(image_path).convert("RGB")
    img_np = np.array(image)

    # ==================================================
    #  FILE HASH (ABSOLUTE IDENTITY)
    # ==================================================
    with open(image_path, "rb") as f:
        img_hash = hashlib.sha256(f.read()).hexdigest()

    # ==================================================
    #  TRADITIONAL FEATURES (INFRINGEMENT ENGINE)
    # ==================================================

    # PHASH
    phash = imagehash.phash(image)
    phash_vector = phash.hash.flatten().astype(float)
    phash_vector /= (np.linalg.norm(phash_vector) + 1e-8)

    # COLOR HISTOGRAM
    hist = cv2.calcHist(
        [img_np], [0, 1, 2], None,
        [8, 8, 8], [0, 256, 0, 256, 0, 256]
    )
    hist = cv2.normalize(hist, None).flatten()

    # EDGE STRUCTURE
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.array([edges.mean() / 255.0])

    traditional_vector = np.concatenate([
        phash_vector * 0.5,
        hist * 0.3,
        edge_density * 0.2
    ])

    # ==================================================
    #  CNN FEATURES (VISUAL SIMILARITY ONLY)
    # ==================================================
    try:
        cnn_img = image.resize(CNN_INPUT_SIZE)
        cnn_arr = img_to_array(cnn_img)
        cnn_arr = np.expand_dims(cnn_arr, axis=0)
        cnn_arr = preprocess_input(cnn_arr)

        cnn_features = _CNN_MODEL.predict(cnn_arr, verbose=0)[0]
        cnn_features /= (np.linalg.norm(cnn_features) + 1e-8)

    except Exception:
        cnn_features = np.zeros(1280)

    # ==================================================
    #  RETURN (BACKWARD COMPATIBLE)
    # ==================================================
    return {
        "hash": img_hash,
        "vector": traditional_vector.tolist(),          # infringement
        "matrix": traditional_vector.reshape(1, -1).tolist(),
        "cnn_vector": cnn_features.tolist()             # visual only
    }
