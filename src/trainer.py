import re
from pathlib import Path

import joblib
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC


def clean_resume_text(text):
    """Lowercase, strip special chars, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def main():
    """Train a resume classifier and update the job description dataset."""
    resumes_path = Path("data") / "processed" / "resumes_clean.csv"
    job_desc_path = Path("data") / "processed" / "job_descriptions_clean.csv"
    models_dir = Path("models")

    print("Step 1/9: Loading resumes_clean.csv...")
    if not resumes_path.exists():
        raise FileNotFoundError(f"Missing dataset: {resumes_path}")

    resumes_df = pd.read_csv(resumes_path, usecols=["Resume", "Category"])
    if resumes_df.empty:
        raise ValueError("Resume dataset is empty.")

    print("Step 2/9: Dropping empty Resume/Category rows...")
    resumes_df = resumes_df.dropna(subset=["Resume", "Category"])
    resumes_df = resumes_df[resumes_df["Resume"].astype(str).str.strip().ne("")]
    resumes_df = resumes_df[resumes_df["Category"].astype(str).str.strip().ne("")]

    total_rows = len(resumes_df)
    unique_categories = resumes_df["Category"].nunique()
    print(f"Rows loaded: {total_rows}")
    print(f"Unique categories: {unique_categories}")

    print("Step 3/9: Cleaning resume text...")
    resumes_df["clean_resume"] = resumes_df["Resume"].astype(str).apply(clean_resume_text)
    resumes_df = resumes_df[resumes_df["clean_resume"].str.len() > 0]
    if resumes_df.empty:
        raise ValueError("No usable rows after cleaning resume text.")

    print("Step 4/9: Encoding labels...")
    label_encoder = LabelEncoder()
    labels = label_encoder.fit_transform(resumes_df["Category"])

    print("Step 5/9: Vectorizing text with TF-IDF (word + char)...")
    word_vectorizer = TfidfVectorizer(
        max_features=20000,
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
    word_features = word_vectorizer.fit_transform(resumes_df["clean_resume"])
    char_features = char_vectorizer.fit_transform(resumes_df["clean_resume"])
    features = hstack([word_features, char_features])

    print("Step 6/9: Running cross-validation (5-fold, macro F1)...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_model = LinearSVC(class_weight="balanced")
    cv_scores = cross_val_score(
        cv_model,
        features,
        labels,
        cv=cv,
        scoring="f1_macro",
        n_jobs=-1,
    )
    print(
        "CV macro F1 scores: "
        + ", ".join(f"{score:.3f}" for score in cv_scores)
    )
    print(f"CV macro F1 mean: {cv_scores.mean():.3f}")

    print("Step 7/9: Splitting train/test data (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    print("Step 8/9: Training LinearSVC model...")
    model = LinearSVC(class_weight="balanced")
    model.fit(X_train, y_train)

    train_accuracy = model.score(X_train, y_train)
    test_preds = model.predict(X_test)
    test_accuracy = accuracy_score(y_test, test_preds)
    print(f"Training accuracy: {train_accuracy:.4f}")
    print(f"Test accuracy: {test_accuracy:.4f}")

    print("Classification report:")
    print(
        classification_report(
            y_test,
            test_preds,
            target_names=label_encoder.classes_,
            zero_division=0,
        )
    )

    print("Step 9/9: Saving model artifacts to models/...")
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, models_dir / "job_classifier.pkl")
    joblib.dump(
        {"word": word_vectorizer, "char": char_vectorizer},
        models_dir / "tfidf_vectorizer.pkl",
    )
    joblib.dump(label_encoder, models_dir / "label_encoder.pkl")

    # Update job descriptions with combined full_jd_text column
    print("Updating job_descriptions_clean.csv with full_jd_text...")
    if not job_desc_path.exists():
        raise FileNotFoundError(f"Missing dataset: {job_desc_path}")

    job_desc_df = pd.read_csv(job_desc_path)
    for column_name in ["Job Description", "skills", "Responsibilities"]:
        if column_name not in job_desc_df.columns:
            raise ValueError(f"Missing column in job descriptions: {column_name}")

    job_desc_df["full_jd_text"] = (
        job_desc_df["Job Description"].fillna("")
        + " "
        + job_desc_df["skills"].fillna("")
        + " "
        + job_desc_df["Responsibilities"].fillna("")
    ).str.strip()

    job_desc_df.to_csv(job_desc_path, index=False)
    print("Job description file updated successfully.")

    print("Training complete! Model saved to models/ folder")


if __name__ == "__main__":
    main()
