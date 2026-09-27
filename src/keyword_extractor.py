from __future__ import annotations

from typing import List

from rake_nltk import Rake
from sklearn.feature_extraction.text import TfidfVectorizer


def extract_keywords_tfidf(text: str, top_n: int = 20) -> List[str]:
    """Extract top N unique terms using TF-IDF term weighting."""
    if not text or not text.strip():
        return []

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform([text])
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]

    ranked = sorted(zip(feature_names, scores), key=lambda item: item[1], reverse=True)
    keywords = [term for term, score in ranked if score > 0]
    return keywords[:top_n]


def extract_keywords_rake(text: str, top_n: int = 20) -> List[str]:
    """Extract top N multi-word phrases using RAKE."""
    if not text or not text.strip():
        return []

    rake = Rake()
    rake.extract_keywords_from_text(text)

    ranked_phrases = rake.get_ranked_phrases_with_scores()
    keywords = [phrase for _, phrase in ranked_phrases]
    return keywords[:top_n]


def extract_keywords(text: str, top_n: int = 20) -> List[str]:
    """Combine and deduplicate keywords from TF-IDF and RAKE."""
    tfidf_keywords = extract_keywords_tfidf(text, top_n=top_n)
    rake_keywords = extract_keywords_rake(text, top_n=top_n)

    # Preserve order while deduplicating between methods
    seen = set()
    combined: List[str] = []
    for keyword in tfidf_keywords + rake_keywords:
        normalized = keyword.lower().strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            combined.append(keyword)

    return combined[:top_n]


def find_missing_keywords(resume_text: str, jd_keywords: List[str]) -> List[str]:
    """Find JD keywords that are absent from the resume text."""
    if not resume_text or not resume_text.strip():
        return jd_keywords

    resume_lower = resume_text.lower()
    missing: List[str] = []
    for keyword in jd_keywords:
        if keyword and keyword.lower() not in resume_lower:
            missing.append(keyword)

    return missing
