from .embedder import get_similarity_score
from .keyword_extractor import extract_keywords, find_missing_keywords
from .preprocessor import preprocess


def _count_words(text):
    if not text or not text.strip():
        return 0
    return len(text.split())


def _score_label(score):
    if score >= 80:
        return "Excellent Match"
    if score >= 60:
        return "Good Match"
    if score >= 40:
        return "Fair Match"
    return "Needs Work"


def _score_color(score):
    if score >= 80:
        return "#16A34A"
    if score >= 60:
        return "#2563EB"
    if score >= 40:
        return "#D97706"
    return "#DC2626"


def generate_suggestions(missing_keywords):
    """Return up to 5 human-readable improvement tips from missing keywords."""
    if not missing_keywords:
        return ["Great job! Your resume already covers the key job requirements."]

    suggestions = []
    for keyword in missing_keywords[:5]:
        keyword_clean = keyword.strip()
        if not keyword_clean:
            continue
        suggestions.append(
            f"Consider adding {keyword_clean} to your skills or experience sections"
        )

    if not suggestions:
        return ["Consider expanding your resume with relevant skills from the job post."]

    return suggestions


def analyze(resume_text, job_description, model):
    """Run the full resume-vs-JD analysis pipeline and return results dict."""
    resume_clean = preprocess(resume_text)
    jd_clean = preprocess(job_description)

    score = get_similarity_score(resume_clean, jd_clean, model)

    jd_keywords = extract_keywords(job_description, top_n=20)
    missing_keywords = find_missing_keywords(resume_text or "", jd_keywords)
    suggestions = generate_suggestions(missing_keywords)

    return {
        "score": score,
        "score_label": _score_label(score),
        "score_color": _score_color(score),
        "missing_keywords": missing_keywords,
        "jd_keywords": jd_keywords,
        "suggestions": suggestions[:5],
        # Word counts on original text, not preprocessed
        "resume_word_count": _count_words(resume_text or ""),
        "jd_word_count": _count_words(job_description or ""),
    }
