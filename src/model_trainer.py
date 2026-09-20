"""Step 2: train and evaluate the ResumeFit AI job-category classifier."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC


def train_classifier(resumes_path: Path, models_dir: Path) -> None:
    """Build TF-IDF features, train LinearSVC, evaluate, and save artifacts."""
    print("\n[3/3] Training job-category classifier")
    resumes = pd.read_csv(resumes_path)
    if resumes.empty:
        raise ValueError("The cleaned resume dataset is empty.")

    label_encoder = LabelEncoder()
    labels = label_encoder.fit_transform(resumes["Category"])

    word_vectorizer = TfidfVectorizer(
        max_features=20_000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
    )
    char_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=2,
        max_df=0.95,
    )
    word_features = word_vectorizer.fit_transform(resumes["Resume"])
    char_features = char_vectorizer.fit_transform(resumes["Resume"])
    features = hstack([word_features, char_features])
    print(f"Word features: {word_features.shape}")
    print(f"Character features: {char_features.shape}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(
        LinearSVC(class_weight="balanced"),
        features,
        labels,
        cv=cv,
        scoring="f1_macro",
        n_jobs=-1,
    )
    print(f"5-fold macro F1: {cv_scores.mean():.3f}")

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )
    model = LinearSVC(class_weight="balanced")
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    print(f"Training accuracy: {model.score(x_train, y_train):.4f}")
    print(f"Test accuracy: {accuracy_score(y_test, predictions):.4f}")
    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            target_names=label_encoder.classes_,
            zero_division=0,
        )
    )

    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, models_dir / "job_classifier.pkl")
    joblib.dump(
        {"word": word_vectorizer, "char": char_vectorizer},
        models_dir / "tfidf_vectorizer.pkl",
    )
    joblib.dump(label_encoder, models_dir / "label_encoder.pkl")
    print(f"Saved model artifacts to: {models_dir}")


def main() -> None:
    """Run model training from the command line."""
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Train and evaluate the ResumeFit AI classifier."
    )
    parser.add_argument(
        "--resumes-path",
        type=Path,
        default=root / "data" / "processed" / "resumes_clean.csv",
    )
    parser.add_argument("--models-dir", type=Path, default=root / "models")
    args = parser.parse_args()
    train_classifier(args.resumes_path, args.models_dir)


if __name__ == "__main__":
    main()
