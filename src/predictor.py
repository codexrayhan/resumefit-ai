import re
from pathlib import Path

import joblib
import numpy as np
from scipy.sparse import hstack


def clean_resume_text(text):
    """Clean resume text identically to the training pipeline."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_classifier():
    """Load trained model, vectorizers, and label encoder from models/."""
    models_dir = Path("models")

    model_path = models_dir / "job_classifier.pkl"
    vec_path = models_dir / "tfidf_vectorizer.pkl"
    le_path = models_dir / "label_encoder.pkl"

    if not (model_path.exists() and vec_path.exists() and le_path.exists()):
        print("Warning: One or more classifier files missing in models/.")
        return None, None, None

    try:
        model = joblib.load(model_path)
        vectorizers = joblib.load(vec_path)
        label_encoder = joblib.load(le_path)
        return model, vectorizers, label_encoder
    except Exception as e:
        print(f"Error loading classifier: {e}")
        return None, None, None


def predict_job_roles(resume_text, model, vectorizers, label_encoder, top_n=3):
    """Predict top N job roles with confidence scores for a resume."""
    if not resume_text or not str(resume_text).strip():
        return []

    if model is None or vectorizers is None or label_encoder is None:
        return []

    try:
        cleaned_text = clean_resume_text(resume_text)

        word_features = vectorizers["word"].transform([cleaned_text])
        char_features = vectorizers["char"].transform([cleaned_text])
        features = hstack([word_features, char_features])

        decision_scores = model.decision_function(features)[0]

        top_indices = np.argsort(decision_scores)[::-1][:top_n]
        top_scores = decision_scores[top_indices]

        # Shift so minimum is 0, then softmax over top N only
        top_scores = top_scores - top_scores.min()
        exp_scores = np.exp(top_scores)
        softmax_scores = exp_scores / exp_scores.sum()

        results = []
        for i, idx in enumerate(top_indices):
            raw_role = str(label_encoder.inverse_transform([idx])[0])
            role = raw_role.replace("-", " ").title()
            confidence = round(float(softmax_scores[i]) * 100, 1)
            results.append({"role": role, "confidence": confidence})

        return results
    except Exception as e:
        print(f"Error during job role prediction: {e}")
        return []
