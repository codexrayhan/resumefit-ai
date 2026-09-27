import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

_MODEL_CACHE = None


def load_model():
    """Load the SBERT model once and cache it for reuse."""
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        print("Loading SBERT model...")
        _MODEL_CACHE = SentenceTransformer("all-MiniLM-L6-v2")
        print("SBERT model ready.")
    return _MODEL_CACHE


def get_embedding(text, model):
    """Encode text into a 384-dim vector, returning zeros for empty input."""
    if not text or not str(text).strip():
        return np.zeros(384)
    return model.encode(text)


def get_similarity_score(text1, text2, model):
    """Return cosine similarity between two texts as a 0-100 score."""
    if not text1 or not str(text1).strip() or not text2 or not str(text2).strip():
        return 0.0

    emb1 = get_embedding(text1, model)
    emb2 = get_embedding(text2, model)

    sim = cosine_similarity([emb1], [emb2])[0][0]

    # Clip to [0, 100] — cosine sim can slightly exceed 1.0 from float rounding
    score = min(100.0, max(0.0, float(sim) * 100))
    return round(score, 1)
