import numpy as np
import re
import librosa
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from functools import lru_cache

# ============================================================
# TYPE THRESHOLDS
# ============================================================

THRESHOLDS = {
    "text": 70,
    "image": 75,
    "audio": 65
}

# ============================================================
# SAFE COSINE (OPTIMIZED)
# ============================================================

def cosine_safe(v1, v2):
    try:
        v1 = np.asarray(v1, dtype=np.float32)
        v2 = np.asarray(v2, dtype=np.float32)

        if v1.size == 0 or v2.size == 0 or v1.shape != v2.shape:
            return 0.0

        dot_product = np.dot(v1, v2)
        norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        
        if norm_product == 0:
            return 0.0
            
        return float((dot_product / norm_product) * 100)
    except:
        return 0.0

# ============================================================
# 🔥 TEXT NORMALIZATION (CACHED) - MATCHES FINGERPRINT
# ============================================================

@lru_cache(maxsize=1024)
def normalize_text_cached(text: str) -> str:
    """Cached version for repeated texts - matches fingerprint normalization"""
    return _normalize_text_impl(text)

def _normalize_text_impl(text: str) -> str:
    """
    Internal implementation - MUST MATCH fingerprint_text.py normalization
    Simple normalization: lowercase + collapse whitespace
    """
    if not text:
        return ""
    
    text = text.lower()
    text = " ".join(text.split())  # Collapse all whitespace
    return text.strip()

def normalize_text(text: str) -> str:
    """
    Wrapper that uses cache for hashable inputs
    IMPORTANT: This matches the fingerprint normalization exactly
    """
    try:
        return normalize_text_cached(text)
    except:
        return _normalize_text_impl(text)

# ============================================================
# 🔥 OPTIMIZED TOKEN OVERLAP
# ============================================================

def token_overlap_ratio(text1, text2):
    """Fast set-based token overlap"""
    s1 = set(text1.split())
    s2 = set(text2.split())
    
    if not s1 or not s2:
        return 0.0
    
    intersection_len = len(s1 & s2)
    union_len = len(s1) + len(s2) - intersection_len
    
    return intersection_len / union_len

# ============================================================
# 🔥 OPTIMIZED SEQUENCE SIMILARITY (10x FASTER)
# ============================================================

def sequence_similarity(text1, text2):
    """
    Optimized LCS with early termination and length limits
    """
    tokens1 = text1.split()
    tokens2 = text2.split()
    
    if not tokens1 or not tokens2:
        return 0.0
    
    m, n = len(tokens1), len(tokens2)
    max_len = max(m, n)
    
    # Skip expensive LCS for very long sequences
    if max_len > 500:
        sample_size = 300
        if m > sample_size:
            step = m // sample_size
            tokens1 = tokens1[::step][:sample_size]
            m = len(tokens1)
        if n > sample_size:
            step = n // sample_size
            tokens2 = tokens2[::step][:sample_size]
            n = len(tokens2)
    
    # Space-optimized LCS
    if m < n:
        tokens1, tokens2 = tokens2, tokens1
        m, n = n, m
    
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if tokens1[i-1] == tokens2[j-1]:
                curr[j] = prev[j-1] + 1
            else:
                curr[j] = max(prev[j], curr[j-1])
        prev, curr = curr, prev
    
    lcs = prev[n]
    return lcs / max_len

# ============================================================
# CHARACTER N-GRAM (OPTIMIZED)
# ============================================================

def char_ngram_similarity(t1, t2, n=5):
    """Optimized character n-gram with early exit"""
    len1, len2 = len(t1), len(t2)
    
    if len1 < n or len2 < n:
        return 0.0
    
    # Early exit for very different lengths
    if min(len1, len2) / max(len1, len2) < 0.5:
        return 0.0
    
    g1 = {t1[i:i+n] for i in range(len1 - n + 1)}
    g2 = {t2[i:i+n] for i in range(len2 - n + 1)}
    
    if not g1 or not g2:
        return 0.0
    
    intersection_len = len(g1 & g2)
    union_len = len(g1) + len(g2) - intersection_len
    
    return intersection_len / union_len

# ============================================================
# 🔥 IMPROVED TF-IDF (CACHED VECTORIZER)
# ============================================================

def build_tfidf_vectors(text1, text2):
    """Optimized TF-IDF with reusable vectorizer"""
    corpus = [text1, text2]
    
    try:
        vectorizer = TfidfVectorizer(
            max_features=3000,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            lowercase=False,
            dtype=np.float32
        )
        
        tfidf = vectorizer.fit_transform(corpus).toarray()
        return tfidf[0], tfidf[1]
    
    except:
        # Fast fallback
        words = set(text1.split() + text2.split())
        if not words:
            return np.array([], dtype=np.float32), np.array([], dtype=np.float32)
        
        word_to_idx = {w: i for i, w in enumerate(words)}
        vec_size = len(words)
        
        vec1 = np.zeros(vec_size, dtype=np.float32)
        vec2 = np.zeros(vec_size, dtype=np.float32)
        
        for word in text1.split():
            vec1[word_to_idx[word]] += 1
        for word in text2.split():
            vec2[word_to_idx[word]] += 1
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 > 0:
            vec1 /= norm1
        if norm2 > 0:
            vec2 /= norm2
        
        return vec1, vec2

# ============================================================
# 🔥 EXACT CONTENT DETECTOR (OPTIMIZED)
# ============================================================

def exact_content_ratio(text1, text2):
    """
    Optimized exact match with early exit
    """
    len1 = len(text1)
    len2 = len(text2)
    
    if len1 == 0 or len2 == 0:
        return 0.0
    
    # Early exit if lengths are very different
    ratio = min(len1, len2) / max(len1, len2)
    if ratio < 0.7:
        return ratio * 0.5
    
    c1 = text1.replace(' ', '').replace('\n', '').replace('\t', '')
    c2 = text2.replace(' ', '').replace('\n', '').replace('\t', '')
    
    if not c1 or not c2:
        return 0.0
    
    min_len = min(len(c1), len(c2))
    matches = sum(1 for a, b in zip(c1[:min_len], c2[:min_len]) if a == b)
    
    return matches / max(len(c1), len(c2))

# ============================================================
# 🔥 TEXT EXTRACTION FROM FINGERPRINT (FIXED)
# ============================================================

def extract_text_from_fingerprint(fp):
    """
    Extract normalized text from fingerprint
    Works with the fingerprint_text.py output format
    """
    if not fp:
        return ""
    
    # Priority order: normalized_text (what we add), then fallbacks
    text = (fp.get("normalized_text") or 
            fp.get("raw_text") or 
            fp.get("text") or "")
    
    if not text:
        return ""
    
    # Text is already normalized in fingerprint, but ensure consistency
    # Only apply normalization if text wasn't already normalized
    if "normalized_text" in fp:
        # Already normalized, return as-is
        return text
    else:
        # Apply normalization for backward compatibility
        return normalize_text(text)

# ============================================================
# MFCC CLEANUP (UNCHANGED)
# ============================================================

def _clean_mfcc(mfcc):
    if mfcc is None:
        return None

    mfcc = np.asarray(mfcc, dtype=np.float32)
    if mfcc.ndim != 2 or mfcc.shape[1] < 10:
        return None

    energy = np.mean(np.abs(mfcc), axis=0)
    mask = energy > np.percentile(energy, 35)
    mfcc = mfcc[:, mask]

    if mfcc.shape[1] < 10:
        return None

    return (mfcc - np.mean(mfcc)) / (np.std(mfcc) + 1e-8)

# ============================================================
# DTW (UNCHANGED)
# ============================================================

def dtw_similarity(seq1, seq2):
    try:
        mfcc1 = _clean_mfcc(seq1)
        mfcc2 = _clean_mfcc(seq2)

        if mfcc1 is None or mfcc2 is None:
            return 0.0

        D, wp = librosa.sequence.dtw(
            mfcc1.T,
            mfcc2.T,
            metric="cosine",
            subseq=True
        )

        dist = np.min(D[-1])
        aligned = len(wp)
        min_frames = min(mfcc1.shape[1], mfcc2.shape[1])
        align_ratio = aligned / max(min_frames, 1)

        score = 100 * np.exp(-dist / 35.0) * min(1.0, align_ratio)
        return round(float(score), 2)

    except:
        return 0.0

# ============================================================
# 🔥 OPTIMIZED SIMILARITY ENGINE (FIXED FOR TEXT FINGERPRINTS)
# ============================================================

def compute_similarity_score(fp1, fp2, file_type: str = None):
    """
    Optimized similarity computation with lazy evaluation
    FIXED: Properly works with fingerprint_text.py output
    """

    if not fp1 or not fp2:
        return 0.0

    # ----------------------------------------------------------
    # 1️⃣ EXACT HASH MATCH (FAST PATH)
    # ----------------------------------------------------------
    if fp1.get("hash") and fp1.get("hash") == fp2.get("hash"):
        return 100.0

    # ----------------------------------------------------------
    # 2️⃣ OPTIMIZED TEXT SIMILARITY (FIXED)
    # ----------------------------------------------------------
    if file_type == "text":

        # 🔥 FIXED: Extract text properly from fingerprints
        raw1 = extract_text_from_fingerprint(fp1)
        raw2 = extract_text_from_fingerprint(fp2)

        if not raw1 or not raw2:
            # Fallback: Try to compare TF-IDF vectors if no text
            tfidf_score = cosine_safe(fp1.get("vector", []), fp2.get("vector", []))
            semantic_score = cosine_safe(fp1.get("nlp_vector", []), fp2.get("nlp_vector", []))
            
            if tfidf_score > 0 or semantic_score > 0:
                return round((tfidf_score * 0.6 + semantic_score * 0.4), 2)
            
            return 0.0

        # === STAGED EVALUATION (compute only what's needed) ===
        
        # Stage 1: Quick checks first
        exact_ratio = exact_content_ratio(raw1, raw2)
        
        # Fast path: Exact match
        if exact_ratio > 0.95:
            return 100.0
        
        # Stage 2: Lexical features (cheap)
        overlap = token_overlap_ratio(raw1, raw2)
        char_sim = char_ngram_similarity(raw1, raw2, n=5)
        
        # Fast path: Exact copy detected
        if overlap > 0.90 and char_sim > 0.85:
            return 100.0
        
        # Fast path: Clearly different
        if overlap < 0.15 and char_sim < 0.15:
            v1, v2 = build_tfidf_vectors(raw1, raw2)
            tfidf_score = cosine_safe(v1, v2)
            if tfidf_score < 15:
                return round(tfidf_score * 0.5, 2)
        
        # Stage 3: Expensive computations (only when needed)
        v1, v2 = build_tfidf_vectors(raw1, raw2)
        tfidf_score = cosine_safe(v1, v2)
        
        # High copy path (skip sequence calculation)
        if exact_ratio > 0.80 or (overlap > 0.75):
            seq_sim = sequence_similarity(raw1, raw2)
            if seq_sim > 0.70:
                return round(min(95.0 + exact_ratio * 5, 100.0), 2)
        
        # Stage 4: Full analysis for edge cases
        seq_sim = sequence_similarity(raw1, raw2)
        
        semantic_score = cosine_safe(
            fp1.get("nlp_vector", []),
            fp2.get("nlp_vector", [])
        )

        # === DECISION LOGIC ===
        
        # Partial copy
        if overlap > 0.50 and char_sim > 0.45:
            final = (
                tfidf_score * 0.50 +
                overlap * 100 * 0.25 +
                char_sim * 100 * 0.15 +
                seq_sim * 100 * 0.10
            )
            return round(float(min(final, 95.0)), 2)
        
        # Clearly different
        if tfidf_score < 15 and overlap < 0.15 and char_sim < 0.15:
            return round(tfidf_score * 0.5, 2)
        
        # Similar but different
        if overlap < 0.20 and char_sim < 0.20:
            semantic_score *= 0.3
        
        # Standard combination
        final = (
            tfidf_score * 0.55 +
            semantic_score * 0.15 +
            overlap * 100 * 0.12 +
            char_sim * 100 * 0.10 +
            seq_sim * 100 * 0.08
        )
        
        final = min(final, tfidf_score + 20)
        
        return round(float(min(final, 100.0)), 2)

    # ----------------------------------------------------------
    # 3️⃣ IMAGE (OPTIMIZED)
    # ----------------------------------------------------------
    if file_type == "image":
        return round(cosine_safe(fp1.get("vector"), fp2.get("vector")), 2)

    # ----------------------------------------------------------
    # 4️⃣ AUDIO (UNCHANGED)
    # ----------------------------------------------------------
    if file_type == "audio":

        mfcc_score = cosine_safe(fp1.get("vector"), fp2.get("vector"))
        dtw_score  = dtw_similarity(fp1.get("matrix"), fp2.get("matrix"))
        dl_score   = cosine_safe(fp1.get("dl_vector"), fp2.get("dl_vector"))

        d1 = fp1.get("duration", 0)
        d2 = fp2.get("duration", 0)

        trimmed = d1 > 0 and d2 > 0 and min(d1, d2) / max(d1, d2) < 0.85

        if trimmed and dtw_score < 60:
            return 0.0

        final = (
            dtw_score * 0.45 +
            dl_score * 0.35 +
            mfcc_score * 0.20
        )

        return round(float(final), 2)

    return 0.0

# ============================================================
# VIOLATION CHECK
# ============================================================

def is_violation(similarity, file_type: str):
    """Check if similarity score exceeds threshold for file type"""
    return file_type in THRESHOLDS and similarity >= THRESHOLDS[file_type]

# ============================================================
# LEGACY WRAPPER
# ============================================================

def compute_similarity(fp1, fp2, file_type=None):
    """Legacy wrapper for backward compatibility"""
    return compute_similarity_score(fp1, fp2, file_type)

# ============================================================
# 🔥 OPTIMIZED COMPARISON HELPER
# ============================================================

def compare_files(fp1, fp2, file_type="text", verbose=True):
    """
    Compare two fingerprints with optional detailed breakdown
    """
    score = compute_similarity_score(fp1, fp2, file_type)
    violation = is_violation(score, file_type)
    
    result = {
        "similarity": score,
        "is_violation": violation,
        "threshold": THRESHOLDS.get(file_type, 0),
        "file_type": file_type
    }
    
    if verbose and file_type == "text":
        raw1 = extract_text_from_fingerprint(fp1)
        raw2 = extract_text_from_fingerprint(fp2)
        
        if raw1 and raw2:
            result["details"] = {
                "exact_match": exact_content_ratio(raw1, raw2),
                "token_overlap": token_overlap_ratio(raw1, raw2),
                "char_ngram": char_ngram_similarity(raw1, raw2),
                "sequence_preservation": sequence_similarity(raw1, raw2)
            }
    
    return result

# ============================================================
# 🔥 CACHE MANAGEMENT
# ============================================================

def clear_cache():
    """Clear normalization cache to free memory"""
    normalize_text_cached.cache_clear()

def get_cache_info():
    """Get cache statistics"""
    return normalize_text_cached.cache_info()