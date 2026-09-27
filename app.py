import os
import sys
import tempfile

sys.path.insert(0, ".")

from flask import Flask, request, jsonify, render_template, redirect
from werkzeug.utils import secure_filename

from src.parser import extract_text
from src.scorer import analyze
from src.embedder import load_model
from src.predictor import load_classifier, predict_job_roles

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["TEMPLATES_AUTO_RELOAD"] = False

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in ALLOWED_EXTENSIONS


print("Loading models…")

try:
    sbert_model = load_model()
except Exception as e:
    print(f"Failed to load SBERT model: {e}")
    sys.exit(1)

# Classifier is optional — missing model files produce (None, None, None)
classifier, vectorizers, label_encoder = load_classifier()

print("Models loaded. Starting server…")


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/docs", methods=["GET"])
def docs_page():
    return render_template("docs.html")


@app.route("/help", methods=["GET"])
def help_page():
    return redirect("/docs", code=301)


@app.route("/privacy", methods=["GET"])
def privacy_page():
    return render_template("privacy.html")


@app.route("/security", methods=["GET"])
def security_page():
    return render_template("security.html")


@app.route("/terms", methods=["GET"])
def terms_page():
    return render_template("terms.html")


@app.route("/analyze", methods=["POST"])
def analyze_resume():
    job_description = request.form.get("job_description", "").strip()
    if not job_description:
        return jsonify({"error": "Job description cannot be empty."}), 400

    if len(job_description.split()) < 20:
        return jsonify({"error": "Job description is too short. Please provide at least 20 words."}), 400

    resume_text = request.form.get("resume_text", "").strip()
    uploaded_file = request.files.get("file")

    if not resume_text and not uploaded_file:
        return jsonify({"error": "No file or text was provided."}), 400

    if uploaded_file and not resume_text:
        if uploaded_file.filename == "":
            return jsonify({"error": "No file was selected."}), 400

        if not _allowed_file(uploaded_file.filename):
            return jsonify(
                {
                    "error": (
                        "Unsupported file type. "
                        "Please upload a PDF, DOCX, or TXT file."
                    )
                }
            ), 400

        tmp_dir = tempfile.mkdtemp()
        safe_name = secure_filename(uploaded_file.filename)
        tmp_path = os.path.join(tmp_dir, safe_name)

        try:
            uploaded_file.save(tmp_path)

            with open(tmp_path, "rb") as fh:
                resume_text = extract_text(fh, safe_name)

            if not resume_text or not resume_text.strip():
                return jsonify({"error": "Could not read text from this file."}), 422
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            try:
                os.rmdir(tmp_dir)
            except OSError:
                pass

    result = analyze(resume_text, job_description, sbert_model)

    if classifier is not None:
        roles = predict_job_roles(
            resume_text,
            classifier,
            vectorizers,
            label_encoder,
            top_n=3,
        )
    else:
        roles = []

    return jsonify(
        {
            "score":             result["score"],
            "score_label":       result["score_label"],
            "score_color":       result["score_color"],
            "missing_keywords":  result["missing_keywords"],
            "jd_keywords":       result["jd_keywords"],
            "suggestions":       result["suggestions"],
            "resume_word_count": result["resume_word_count"],
            "jd_word_count":     result["jd_word_count"],
            "predicted_roles":   roles,
            "resume_text":       resume_text,
        }
    )


@app.route("/reanalyze", methods=["POST"])
def reanalyze_resume():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    resume_text = (data.get("resume_text") or "").strip()
    job_description = (data.get("job_description") or "").strip()

    if len(resume_text) < 50:
        return jsonify({"error": "Resume text is too short. Please provide at least 50 characters."}), 400

    if len(job_description.split()) < 20:
        return jsonify({"error": "Job description is too short. Please provide at least 20 words."}), 400

    result = analyze(resume_text, job_description, sbert_model)

    if classifier is not None:
        roles = predict_job_roles(
            resume_text,
            classifier,
            vectorizers,
            label_encoder,
            top_n=3,
        )
    else:
        roles = []

    return jsonify(
        {
            "score":             result["score"],
            "score_label":       result["score_label"],
            "score_color":       result["score_color"],
            "missing_keywords":  result["missing_keywords"],
            "jd_keywords":       result["jd_keywords"],
            "suggestions":       result["suggestions"],
            "resume_word_count": result["resume_word_count"],
            "jd_word_count":     result["jd_word_count"],
            "predicted_roles":   roles,
            "resume_text":       resume_text,
        }
    )


@app.route("/health", methods=["POST"])
def health():
    models_loaded = sbert_model is not None
    return jsonify({"status": "ok", "models_loaded": models_loaded})


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File too large. Maximum size is 5MB."}), 413


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "Something went wrong. Please try again."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
