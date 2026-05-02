import librosa
import numpy as np
import hashlib
import os
from typing import Dict, Any

# ================= TF SILENCE =================
import os as _os
_os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
_os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import tensorflow as tf
import tensorflow_hub as hub

tf.get_logger().setLevel("ERROR")
tf.autograph.set_verbosity(0)

# ================= CONSTANTS =================
SR = 16000
N_MFCC = 20
MIN_AUDIO_SAMPLES = 4000
MAX_AUDIO_SEC = 12

WINDOW_FRAMES = 10   # ~1 second
HOP_FRAMES = 5

# ================= LOAD MODEL ONCE =================
_VGGISH_MODEL = hub.load("https://tfhub.dev/google/vggish/1")

# ============================================================
# ✔ PREPROCESS AUDIO
# ============================================================

def preprocess_signal(y: np.ndarray) -> np.ndarray:
    y, _ = librosa.effects.trim(y, top_db=25)

    rms = np.sqrt(np.mean(y ** 2))
    if rms > 0:
        y = y / rms

    y = librosa.effects.preemphasis(y)
    return y.astype(np.float32)


# ============================================================
# ✔ TRIM-ROBUST DEEP EMBEDDING
# ============================================================

def _deep_audio_embedding(y: np.ndarray) -> np.ndarray:
    """
    ✔ Sliding-window VGGish aggregation
    ✔ Trim invariant
    ✔ Original ≈ Trimmed
    ✔ Different audio ≠ similar
    """
    try:
        y_tf = tf.convert_to_tensor(y, dtype=tf.float32)

        # [frames, 128]
        embeddings = _VGGISH_MODEL(y_tf)

        if embeddings.shape[0] == 0:
            return np.zeros(128, dtype=np.float32)

        embeddings = tf.math.l2_normalize(embeddings, axis=1)

        # Sliding window aggregation
        chunk_vectors = []
        num_frames = embeddings.shape[0]

        for start in range(0, num_frames - WINDOW_FRAMES + 1, HOP_FRAMES):
            chunk = embeddings[start:start + WINDOW_FRAMES]
            chunk_vec = tf.reduce_mean(chunk, axis=0)
            chunk_vec = tf.math.l2_normalize(chunk_vec, axis=0)
            chunk_vectors.append(chunk_vec)

        if not chunk_vectors:
            emb = tf.reduce_mean(embeddings, axis=0)
            emb = tf.math.l2_normalize(emb, axis=0)
            return emb.numpy().astype(np.float32)

        # Max-pooling across chunks (trim-robust)
        stacked = tf.stack(chunk_vectors, axis=0)
        final_emb = tf.reduce_max(stacked, axis=0)
        final_emb = tf.math.l2_normalize(final_emb, axis=0)

        return final_emb.numpy().astype(np.float32)

    except Exception as e:
        print("Audio DL embedding failed:", e)
        return np.zeros(128, dtype=np.float32)


# ============================================================
# ✔ FINAL AUDIO FINGERPRINT
# ============================================================

def fingerprint_audio(audio_path: str) -> Dict[str, Any]:

    if not os.path.exists(audio_path):
        return {"hash": None, "vector": [], "matrix": None, "dl_vector": []}

    # -------- FILE HASH --------
    try:
        with open(audio_path, "rb") as f:
            audio_hash = hashlib.sha256(f.read()).hexdigest()
    except Exception:
        audio_hash = None

    try:
        y, sr = librosa.load(
            audio_path,
            sr=SR,
            mono=True,
            duration=MAX_AUDIO_SEC
        )

        if y is None or len(y) < MIN_AUDIO_SAMPLES:
            return {"hash": audio_hash, "vector": [], "matrix": None, "dl_vector": []}

        y = preprocess_signal(y)

        # -------- MFCC --------
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_seq = mfcc.T

        # -------- DEEP ID --------
        dl_vec = _deep_audio_embedding(y)

        return {
            "hash": audio_hash,
            "vector": mfcc_mean.tolist(),
            "matrix": mfcc_seq.tolist(),
            "dl_vector": dl_vec.tolist()
        }

    except Exception as e:
        print("Audio fingerprint error:", e)
        return {"hash": audio_hash, "vector": [], "matrix": None, "dl_vector": []}
