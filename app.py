import os
import sys
import tempfile
from datetime import timedelta

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, jsonify, render_template, redirect, session
from flask_login import current_user
from werkzeug.utils import secure_filename

from models import db, Analysis
from auth import init_auth
from src.parser import extract_text
from src.scorer import analyze
from src.embedder import load_model
from src.predictor import load_classifier, predict_job_roles

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["TEMPLATES_AUTO_RELOAD"] = False

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///resumefit.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

db.init_app(app)
init_auth(app)

with app.app_context():
    db.create_all()

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
GUEST_LIMIT = 2


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


def _guest_limit_reached() -> bool:
    return (
        not current_user.is_authenticated
        and session.get("guest_uses", 0) >= GUEST_LIMIT
    )


def _limit_response():
    return (
        jsonify(
            {
                "error": "Free limit reached. Please sign in with Google to continue.",
                "login_required": True,
            }
        ),
        403,
    )


def _analysis_response(resume_text, job_description, label="", jd_title=""):
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

    saved = False
    guest_uses_left = None

    if current_user.is_authenticated:
        try:
            db.session.add(
                Analysis(
                    user_id=current_user.id,
                    label=(label or "My resume")[:120],
                    jd_title=(jd_title or "")[:200] or None,
                    score=float(result["score"]),
                    missing_count=len(result["missing_keywords"]),
                    missing_keywords=result["missing_keywords"],
                    predicted_roles=roles,
                )
            )
            db.session.commit()
            saved = True
        except Exception as e:
            db.session.rollback()
            print(f"Could not save analysis: {e}")
    else:
        session.permanent = True
        session["guest_uses"] = session.get("guest_uses", 0) + 1
        guest_uses_left = max(GUEST_LIMIT - session["guest_uses"], 0)

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
            "saved":             saved,
            "guest_uses_left":   guest_uses_left,
        }
    )


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
    if _guest_limit_reached():
        return _limit_response()

    job_description = request.form.get("job_description", "").strip()
    if not job_description:
        return jsonify({"error": "Job description cannot be empty."}), 400

    if len(job_description.split()) < 20:
        return jsonify({"error": "Job description is too short. Please provide at least 20 words."}), 400

    label = request.form.get("resume_label", "").strip()
    jd_title = request.form.get("jd_title", "").strip()

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

    return _analysis_response(resume_text, job_description, label, jd_title)


@app.route("/reanalyze", methods=["POST"])
def reanalyze_resume():
    if _guest_limit_reached():
        return _limit_response()

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    resume_text = (data.get("resume_text") or "").strip()
    job_description = (data.get("job_description") or "").strip()
    label = (data.get("resume_label") or "").strip()
    jd_title = (data.get("jd_title") or "").strip()

    if len(resume_text) < 50:
        return jsonify({"error": "Resume text is too short. Please provide at least 50 characters."}), 400

    if len(job_description.split()) < 20:
        return jsonify({"error": "Job description is too short. Please provide at least 20 words."}), 400

    return _analysis_response(resume_text, job_description, label, jd_title)


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