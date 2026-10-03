# ResumeFit AI — Technical Documentation

## Project status

This document covers Stage 1 of ResumeFit AI: preparing the datasets and
training the job-category classifier. It describes what that stage
implements. The rest of the application is built on top of it and is
described in `README.md` and `API.md`.

### Completed in this stage

- Raw resume and job-description datasets are available under `data/raw/`.
- The datasets are cleaned and written to `data/processed/`.
- Resume categories are normalized and rare categories are filtered.
- Job-description fields are combined into `full_jd_text`.
- Word and character TF-IDF features are generated.
- A balanced `LinearSVC` classifier is trained and evaluated.
- Model artifacts are saved under `models/`.
- The cleaning and training workflow can be run from the command line.

### Built in later stages

- Inference: the saved classifier, vectorizers, and label encoder are loaded
  to predict the top 3 job roles for a resume.
- Resume upload and text extraction for PDF, DOCX, and TXT files.
- Semantic match scoring, keyword extraction, missing-keyword detection, and
  improvement suggestions.
- A Flask application with a web interface.
- Optional Google sign-in, saved analysis history, and a progress dashboard.

### Not yet implemented

- PDF export of the analysis report.
- Automated tests and a repeatable evaluation report.

## 1. Purpose

This workflow covers the first machine-learning stage of ResumeFit AI:

1. Preparing the raw datasets.
2. Cleaning and transforming text.
3. Training and evaluating a job-category classifier.
4. Saving reusable model artifacts.

The workflow is intentionally isolated from the main application. It does not
start Flask, and it can be run on its own from the command line.

## 2. Input datasets

The workflow expects two files in `data/raw/`:

| File | Purpose |
| --- | --- |
| `resumes.csv` | Resume text and job-category labels for classifier training |
| `job_descriptions.csv` | Job descriptions, skills, and responsibilities for later analysis |

The job-description dataset is large, so it is processed incrementally rather
than loaded into memory in one operation.

## 3. Why cleaning is required

Raw datasets are not guaranteed to be ready for machine learning. They may
contain missing values, inconsistent capitalization, punctuation, repeated
whitespace, malformed labels, and records that are too rare to support
stratified evaluation.

The cleaner addresses these issues by:

- removing rows without usable resume text or category labels;
- converting text to lowercase;
- removing non-alphanumeric symbols;
- normalizing whitespace;
- normalizing category labels;
- retaining categories with at least 10 resume examples;
- combining job-description, skills, and responsibilities into `full_jd_text`;
  and
- reading `job_descriptions.csv` in configurable chunks.

These operations reduce noisy or unusable input while preserving the text
needed by the classifier and future job-description analysis.

## 4. Cleaning and processing implementation

The implementation is in [src/data_cleaner.py](src/data_cleaner.py).

Run it from the repository root:

```powershell
python .\src\data_cleaner.py
```

Default outputs:

- `data/processed/resumes_clean.csv`
- `data/processed/job_descriptions_clean.csv`

For a lower-memory run, reduce the chunk size:

```powershell
python .\src\data_cleaner.py --chunk-size 5000
```

The latest cleaning run produced:

- Raw resume rows: **3,446**
- Cleaned resume rows: **2,458**
- Retained categories: **24**
- Processed job-description rows: **1,615,940**

## 5. Training implementation

The implementation is in [src/model_trainer.py](src/model_trainer.py).

Run it after cleaning:

```powershell
python .\src\model_trainer.py
```

The trainer:

1. Loads `resumes_clean.csv`.
2. Encodes category labels using `LabelEncoder`.
3. Builds word-level TF-IDF features with unigrams and bigrams.
4. Builds character-level TF-IDF features with 3–5 character n-grams.
5. Combines both sparse feature matrices.
6. Runs five-fold stratified cross-validation using macro F1.
7. Splits the data into 80% training and 20% testing subsets.
8. Trains a class-balanced `LinearSVC`.
9. Prints accuracy, F1, and a per-category classification report.
10. Saves the trained artifacts.

## 6. Recorded training results

These results were produced from the current cleaned dataset and the current
training configuration:

| Metric | Result |
| --- | ---: |
| Cleaned resumes | 2,458 |
| Categories | 24 |
| Training split | 80% |
| Test split | 20% |
| Test samples | 492 |
| Training accuracy | 100.00% |
| Test accuracy | 71.14% |
| Five-fold macro F1 | 0.660 |

Feature dimensions from the run:

- Word TF-IDF features: **20,000**
- Character TF-IDF features: **77,181**

### Interpretation

Training accuracy measures performance on examples used to fit the model, so
it is expected to be higher. Test accuracy and cross-validation macro F1 are
more useful estimates of performance on unseen resumes.

The `bpo` category had only four test examples in this split. Its individual
score should therefore not be treated as a reliable estimate of general
performance. The overall metrics provide a more useful summary.

## 7. Generated artifacts

The trainer saves these files under `models/`:

- `job_classifier.pkl` — trained `LinearSVC` classifier
- `tfidf_vectorizer.pkl` — word and character TF-IDF vectorizers
- `label_encoder.pkl` — mapping between numeric labels and category names

These three files must be loaded together during inference.

## 8. Reproducibility

The workflow uses fixed random state `42` for the train/test split and
cross-validation shuffling. Results can still vary if the dataset, dependency
versions, or preprocessing rules change.

## 9. Further work

1. Add automated tests and a repeatable evaluation report.
2. Review class imbalance, rare categories, and possible overfitting.
3. Add PDF export of the analysis report.
4. Prepare deployment instructions (production server, HTTPS) once the local
   workflow is stable.

## 10. Limitations

- The classifier reflects the distribution and quality of the source dataset.
- Rare categories provide less reliable per-category metrics.
- Test accuracy does not guarantee performance on every real-world resume.
- This stage trains the job-role classifier only. Inference and the web
  interface are built on top of it in later stages (see `README.md`).