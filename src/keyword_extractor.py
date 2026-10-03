from __future__ import annotations

import re
from itertools import zip_longest
from typing import List

from nltk.corpus import stopwords
from rake_nltk import Rake
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

# Generic job-post words that make poor suggestions on their own,
# e.g. "Consider adding experience to your resume". They are also used as
# phrase boundaries, so "strong communication" becomes "communication".
_NOISE_WORDS = {
    "ability", "able", "also", "apply", "based", "benefits", "candidate",
    "candidates", "company", "day", "demonstrated", "ensure", "environment",
    "etc", "excellent", "experience", "experienced", "good", "great", "help",
    "highly", "ideal", "include", "includes", "including", "job", "join",
    "knowledge", "least", "looking", "minimum", "must", "need", "needs", "new",
    "opportunity", "plus", "position", "preferred", "proven", "provide",
    "related", "relevant", "required", "requirement", "requirements",
    "responsibilities", "responsibility", "role", "salary", "seeking", "skill",
    "skills", "strong", "team", "teams", "time", "understanding", "use",
    "using", "well", "will", "work", "working", "works", "year", "years",
    "across", "around", "within", "per", "via", "like", "various", "several",
    "many", "every", "each", "essential", "important", "range", "variety",
    "hiring", "hire", "grow", "growing", "needed",
}

_STOP_WORDS = set(ENGLISH_STOP_WORDS) | _NOISE_WORDS


def _clean(phrase: str) -> str:
    """Tidy a phrase for display: strip spaces and rejoin 'c ++' as 'c++'."""
    return re.sub(r"\s+([+#]+)", r"\1", phrase.strip())


def _tokens(phrase: str) -> List[str]:
    """Lowercase word tokens; keeps symbols used in names like C++ and C#."""
    return re.findall(r"[a-z0-9+#]+", _clean(phrase).lower())


def _is_noise(tokens: List[str]) -> bool:
    """True if a phrase has no tokens, only digits, or only generic words."""
    if not tokens:
        return True
    return all(token in _NOISE_WORDS or token.isdigit() for token in tokens)


def _contains(longer: List[str], shorter: List[str]) -> bool:
    """True if `shorter` appears as a contiguous run of words inside `longer`."""
    size = len(shorter)
    return any(
        longer[i:i + size] == shorter for i in range(len(longer) - size + 1)
    )


def _drop_redundant(keywords: List[str]) -> List[str]:
    """Remove phrases already covered by a longer phrase in the list.

    Example: ["real", "estate", "real estate"] -> ["real estate"]
    """
    token_lists = [_tokens(keyword) for keyword in keywords]
    kept: List[str] = []
    for i, tokens in enumerate(token_lists):
        covered = any(
            j != i and len(other) > len(tokens) and _contains(other, tokens)
            for j, other in enumerate(token_lists)
        )
        if not covered:
            kept.append(keywords[i])
    return kept


def extract_keywords_tfidf(text: str, top_n: int = 20) -> List[str]:
    """Extract top N unique single terms using TF-IDF term weighting.

    Only single words are used here. Multi-word phrases come from RAKE, which
    respects punctuation and does not join words across commas or full stops.
    """
    if not text or not text.strip():
        return []

    vectorizer = TfidfVectorizer(
        stop_words=sorted(_STOP_WORDS),
        ngram_range=(1, 1),
        token_pattern=r"(?u)\b\w[\w+#]*",
    )
    try:
        tfidf_matrix = vectorizer.fit_transform([text])
    except ValueError:  # the text contained only stop words
        return []

    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]

    ranked = sorted(zip(feature_names, scores), key=lambda item: item[1], reverse=True)
    keywords = [term for term, score in ranked if score > 0]
    return keywords[:top_n]


def extract_keywords_rake(text: str, top_n: int = 20) -> List[str]:
    """Extract top N short phrases (up to 3 words) using RAKE."""
    if not text or not text.strip():
        return []

    rake_stop_words = set(stopwords.words("english")) | _NOISE_WORDS
    rake = Rake(stopwords=rake_stop_words, max_length=3)
    rake.extract_keywords_from_text(text)

    ranked_phrases = rake.get_ranked_phrases_with_scores()
    keywords = [phrase for _, phrase in ranked_phrases]
    return keywords[:top_n]


def extract_keywords(text: str, top_n: int = 20) -> List[str]:
    """Combine TF-IDF and RAKE keywords, then clean up the list.

    Steps: interleave both methods, remove duplicates, drop generic job-post
    words, and drop single words already covered by a longer phrase.
    """
    pool = top_n * 2
    tfidf_keywords = extract_keywords_tfidf(text, top_n=pool)
    rake_keywords = extract_keywords_rake(text, top_n=pool)

    # Interleave so neither method crowds out the other
    merged: List[str] = []
    for pair in zip_longest(rake_keywords, tfidf_keywords):
        merged.extend(keyword for keyword in pair if keyword)

    seen = set()
    candidates: List[str] = []
    for keyword in merged:
        tokens = _tokens(keyword)
        normalized = " ".join(tokens)
        if normalized and normalized not in seen and not _is_noise(tokens):
            seen.add(normalized)
            candidates.append(_clean(keyword))

    return _drop_redundant(candidates)[:top_n]


def _is_present(keyword: str, resume_lower: str) -> bool:
    """Whole-word check that also accepts simple plurals (client -> clients)."""
    tokens = _tokens(keyword)
    if not tokens:
        return True
    body = r"[\s\-/]+".join(re.escape(token) for token in tokens)
    pattern = r"(?<![a-z0-9])" + body + r"(?:s|es)?(?![a-z0-9])"
    return re.search(pattern, resume_lower) is not None


def find_missing_keywords(resume_text: str, jd_keywords: List[str]) -> List[str]:
    """Find JD keywords that are absent from the resume text."""
    if not resume_text or not resume_text.strip():
        return jd_keywords

    resume_lower = resume_text.lower()
    return [
        keyword
        for keyword in jd_keywords
        if keyword and not _is_present(keyword, resume_lower)
    ]