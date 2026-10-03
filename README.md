<div align="center">
  <img src="static/assets/logo.svg" alt="ResumeFit AI Logo" width="120" />
</div>

<h1 align="center">ResumeFit AI</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Flask-3.1.3-black.svg" alt="Flask">
  <img src="https://img.shields.io/badge/scikit--learn-1.8.0-orange.svg" alt="scikit-learn">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

ResumeFit AI analyzes a resume against a job description and returns a match score, missing keywords, improvement suggestions, and predicted job roles. Use it as a guest for 2 free analyses, or sign in with Google to save your history and track how your resume improves over time. All analysis runs locally with no external AI APIs, and your resume text is never stored.

## Features

- Match score from 0 to 100 based on semantic similarity between the resume and job description
- Missing keyword detection showing which job description terms are absent from the resume
- Improvement suggestions as a prioritized action list derived from the missing keywords
- Job role prediction showing the top 3 most likely career categories based on resume content
- Accepts PDF, DOCX, and TXT resume formats
- Google sign-in with a personal dashboard
- Progress tracking: score history and improvement per resume
- Guest mode: 2 free analyses without an account
- No external AI APIs — all inference runs on the user's machine

## How It Works

1. **Upload** — the user uploads a resume (PDF, DOCX, or TXT) and pastes a job description into the text area. Signed-in users can also name the resume and the target job.
2. **Parse** — the system extracts raw text using pdfplumber, PyPDF2 (fallback), or python-docx depending on the file type.
3. **Analyse** — SBERT (all-MiniLM-L6-v2) generates embeddings for both texts and cosine similarity produces a match score from 0 to 100.
4. **Keywords** — TF-IDF and RAKE extract important terms from the job description and identify which are missing from the resume.
5. **Results** — the browser displays the match score, missing keywords, improvement suggestions, and predicted job roles without a page reload.
6. **Save (signed-in users)** — the score, missing keywords, predicted roles, resume name, and job title are saved so the dashboard can chart progress. The resume text itself is never saved.

## Accounts and Data

| User type | Limit | What is stored |
| :--- | :--- | :--- |
| **Guest** | 2 free analyses per browser | Nothing in the database. A counter is kept in a session cookie |
| **Signed-in (Google)** | Unlimited | Name, email, and profile picture URL from the Google account, plus for each analysis: resume name, job title, score, missing keywords, predicted roles, and timestamp |

- Resume text is never stored.
- From the dashboard, a user can delete a single analysis or delete their account and all saved data.
- Google is used only for sign-in. Analysis does not use any external service.
- The guest limit is tracked in a cookie, so it is a soft limit that clearing cookies resets.

## Tech Stack

| Category | Tools |
| :--- | :--- |
| **Frontend** | HTML, CSS, JavaScript, Chart.js (dashboard) |
| **Backend** | Flask 3.1.3, Werkzeug 3.1.8 |
| **Authentication** | Authlib (Google OAuth 2.0 / OpenID Connect), Flask-Login |
| **Database** | Flask-SQLAlchemy, SQLite |
| **Machine Learning** | scikit-learn 1.8.0, scipy 1.17.1, joblib 1.5.3 |
| **NLP** | nltk 3.9.4, rake-nltk 1.0.6, sentence-transformers 5.5.1 |
| **Data Processing** | numpy 2.4.6, pandas 3.0.3, torch 2.12.0 |
| **Document Parsing** | pdfplumber 0.11.9, PyPDF2 3.0.1, python-docx 1.2.0, Pillow 12.2.0 |
| **Configuration** | python-dotenv |

## Quick Start

### Prerequisites

- Python 3.11+
- Git
- A Google account (to create the sign-in credentials)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/codexrayhan/resumefit-ai.git
   cd resumefit-ai
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**

   *Windows (PowerShell):*
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   *Mac/Linux:*
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Download NLTK data**
   ```bash
   python -m nltk.downloader stopwords punkt punkt_tab
   ```

6. **Download the model files**

   Download the three `.pkl` files from [GitHub Releases](https://github.com/codexrayhan/resumefit-ai/releases/latest) and place them in the `models/` folder. See the [Model Files](#model-files) section for details.

7. **Configure Google sign-in** (see the next section)

8. **Run the application**
   ```bash
   python app.py
   ```

   The app runs at `http://localhost:5000`. Open it as `localhost`, not `127.0.0.1`, so the Google redirect matches. The first run downloads the SBERT model (~90 MB) automatically.

## Configure Google Sign-In

1. In [Google Cloud Console](https://console.cloud.google.com), create a project.
2. Set up the **OAuth consent screen** (External) and add your Gmail under **Test users**.
3. Create an **OAuth client ID** of type **Web application**.
4. Add this exact **Authorized redirect URI**:
   ```text
   http://localhost:5000/auth/callback
   ```
5. Copy `.env.example` to `.env` and fill in the values:
   ```text
   SECRET_KEY=a-long-random-string
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```
   Generate a secret key with:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
6. Never commit `.env`. It is listed in `.gitignore`.

While the Google consent screen is in Testing mode, only the emails added as test users can sign in.

## Model Files

The trained model files are distributed via GitHub Releases and are not committed to this repository due to their size.

Download these three files and place them in the `models/` directory:

- `job_classifier.pkl`
- `tfidf_vectorizer.pkl`
- `label_encoder.pkl`

**Releases link:** [https://github.com/codexrayhan/resumefit-ai/releases/latest](https://github.com/codexrayhan/resumefit-ai/releases/latest)

## Training Your Own Model (Optional)

To retrain the classifier, obtain the resume dataset from Kaggle and place the CSV files in `data/raw/`. Training data is not included in this repository due to file size and licensing constraints.

Once the data is in place, run:

```bash
python src/trainer.py
```

This will generate new `.pkl` files in the `models/` directory.

## Project Structure

```text
resumefit-ai/
├── app.py                    # Flask entry point and route definitions
├── auth.py                   # Google sign-in (Authlib) and Flask-Login setup
├── models.py                 # Database tables: User and Analysis
├── requirements.txt          # Pinned package dependencies
├── .env.example              # Template for required environment variables
├── README.md
├── API.md                    # HTTP API reference
├── LICENSE
├── .gitignore
├── instance/                 # Local SQLite database (not in Git)
├── models/                   # Downloaded .pkl model files (not in Git)
│   ├── job_classifier.pkl
│   ├── tfidf_vectorizer.pkl
│   └── label_encoder.pkl
├── src/
│   ├── parser.py             # Extracts text from PDF, DOCX, TXT
│   ├── preprocessor.py       # Cleans and normalises text
│   ├── keyword_extractor.py  # TF-IDF and RAKE keyword extraction
│   ├── embedder.py           # SBERT embeddings and cosine similarity
│   ├── scorer.py             # Main analysis orchestrator
│   ├── predictor.py          # Job role prediction using LinearSVC
│   └── trainer.py            # Standalone model training script
├── static/
│   ├── style.css
│   └── script.js
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   ├── docs.html
│   ├── privacy.html
│   ├── security.html
│   └── terms.html
└── data/
    ├── raw/                  # Original datasets (not in Git)
    └── processed/            # Cleaned CSVs (not in Git)
```

## Model Performance

The job classifier is a LinearSVC model trained on 2,457 resumes across 24 job categories using an 80/20 stratified train/test split. It uses dual TF-IDF features — word-level n-grams and character-level n-grams — combined with `scipy.sparse.hstack`. Hyperparameter search over `C = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]` confirmed that `C = 1.0` is optimal.

| Metric | Score |
| :--- | :--- |
| Test Accuracy | 71.75% |
| CV Macro F1 Mean | 0.659 (5-fold stratified) |
| Best Category (DESIGNER) | F1 0.89 |
| Weakest Category (BPO) | F1 0.00 |

The BPO category scores F1 0.00 not because the model is broken, but because only 4 test samples exist for that category after the train/test split. The training data simply does not have enough BPO examples to support reliable prediction.

## Troubleshooting

- **Model files missing** — download `job_classifier.pkl`, `tfidf_vectorizer.pkl`, and `label_encoder.pkl` from [GitHub Releases](https://github.com/codexrayhan/resumefit-ai/releases/latest) and place them in `models/`.
- **NLTK data errors** — run `python -m nltk.downloader stopwords punkt punkt_tab` with the virtual environment active.
- **PDF cannot be read** — scanned image PDFs contain no extractable text. The system requires a text-based PDF. Convert the document to DOCX or TXT before uploading.
- **Port 5000 already in use** — stop the service using that port, or change the port number in `app.py`. If you change it, update the redirect URI in Google Cloud to match.
- **`KeyError: 'SECRET_KEY'` on startup** — the `.env` file is missing or misnamed. Copy `.env.example` to `.env` and fill it in.
- **`redirect_uri_mismatch` when signing in** — open the app as `http://localhost:5000` and make sure the redirect URI in Google Cloud is exactly `http://localhost:5000/auth/callback`.
- **Google says access is blocked or not allowed** — add your email under **Test users** on the OAuth consent screen.

## Future Work

- PDF export of the gap analysis report including the match score, missing keywords, and improvement suggestions.
- Interactive editing and recalculation on the results page, using the existing `/reanalyze` endpoint.

## License

This project is licensed under the [MIT License](LICENSE).
