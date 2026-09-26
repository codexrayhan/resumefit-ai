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

<p align="center">
  <b><a href="https://huggingface.co/spaces/litch07/resumefit-ai">🚀 Try the Live Demo on Hugging Face Spaces</a></b>
</p>

ResumeFit AI analyzes a resume against a job description and returns a match score, missing keywords, improvement suggestions, and predicted job roles — all running locally with no sign-up or data storage.

## Features

- Match score from 0 to 100 based on semantic similarity between the resume and job description
- Missing keyword detection showing which job description terms are absent from the resume
- Improvement suggestions as a prioritized action list derived from the missing keywords
- Job role prediction showing the top 3 most likely career categories based on resume content
- Accepts PDF, DOCX, and TXT resume formats
- No external APIs — all inference runs on the user's machine

## How It Works

1. **Upload** — the user uploads a resume (PDF, DOCX, or TXT) and pastes a job description into the text area.
2. **Parse** — the system extracts raw text using pdfplumber, PyPDF2 (fallback), or python-docx depending on the file type.
3. **Analyse** — SBERT (all-MiniLM-L6-v2) generates embeddings for both texts and cosine similarity produces a match score from 0 to 100.
4. **Keywords** — TF-IDF and RAKE extract important terms from the job description and identify which are missing from the resume.
5. **Results** — the browser displays the match score, missing keywords, improvement suggestions, and predicted job roles without a page reload.

## Tech Stack

| Category | Tools |
| :--- | :--- |
| **Frontend** | HTML, CSS, JavaScript |
| **Backend** | Flask 3.1.3, Werkzeug 3.1.8 |
| **Machine Learning** | scikit-learn 1.8.0, scipy 1.17.1, joblib 1.5.3 |
| **NLP** | nltk 3.9.4, rake-nltk 1.0.6, sentence-transformers 5.5.1 |
| **Data Processing** | numpy 2.4.6, pandas 3.0.3, torch 2.12.0 |
| **Document Parsing** | pdfplumber 0.11.9, PyPDF2 3.0.1, python-docx 1.2.0, Pillow 12.2.0 |

## Quick Start

### Prerequisites

- Python 3.11+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/litch07/resumefit-ai.git
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

   Download the three `.pkl` files from [GitHub Releases](https://github.com/litch07/resumefit-ai/releases/latest) and place them in the `models/` folder. See the [Model Files](#model-files) section for details.

7. **Run the application**
   ```bash
   python app.py
   ```

   The app runs at `http://localhost:5000`. The first run downloads the SBERT model (~90 MB) automatically.

## Model Files

The trained model files are distributed via GitHub Releases and are not committed to this repository due to their size.

Download these three files and place them in the `models/` directory:

- `job_classifier.pkl`
- `tfidf_vectorizer.pkl`
- `label_encoder.pkl`

**Releases link:** [https://github.com/litch07/resumefit-ai/releases/latest](https://github.com/litch07/resumefit-ai/releases/latest)

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
├── requirements.txt          # Pinned package dependencies
├── README.md
├── API.md                    # HTTP API reference
├── LICENSE
├── .gitignore
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

- **Model files missing** — download `job_classifier.pkl`, `tfidf_vectorizer.pkl`, and `label_encoder.pkl` from [GitHub Releases](https://github.com/litch07/resumefit-ai/releases/latest) and place them in `models/`.
- **NLTK data errors** — run `python -m nltk.downloader stopwords punkt punkt_tab` with the virtual environment active.
- **PDF cannot be read** — scanned image PDFs contain no extractable text. The system requires a text-based PDF. Convert the document to DOCX or TXT before uploading.
- **Port 5000 already in use** — stop the service using that port, or change the port number in `app.py`.

## Future Work

- Interactive editing and recalculation — edit the parsed resume and job description text directly on the results page and get an updated score without re-uploading the file.
- PDF export of the gap analysis report including the match score, missing keywords, and improvement suggestions.

## License

This project is licensed under the [MIT License](LICENSE).
