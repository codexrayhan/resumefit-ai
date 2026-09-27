# ResumeFit AI API Documentation

## Overview
The ResumeFit AI API provides developers with access to a lightweight, AI-powered backend for analyzing how well a resume matches a given job description. It uses NLP techniques and the `all-MiniLM-L6-v2` SBERT model to compute semantic similarity scores, extract missing keywords, provide actionable suggestions, and predict likely job roles based on the resume content. This API is designed to be easily integrated into custom frontends or used for batch processing tasks.

## Base URL
All API requests should be prefixed with the base URL of your local deployment:
```text
http://localhost:5000
```

## Authentication
This API currently does not require authentication. All endpoints are open for local development and usage.

## Rate Limiting
There is no rate limiting enforced on this local deployment. However, since the NLP models run on the CPU, it is recommended to limit concurrent requests to avoid performance degradation.

---

## Endpoints

### UI Endpoints
The following endpoints serve static HTML pages for the web interface and documentation.

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Renders the main user interface (`index.html`). |
| `GET` | `/docs` | Renders the documentation and FAQ page (`docs.html`). Note: `/help` redirects here. |
| `GET` | `/privacy` | Renders the privacy policy page (`privacy.html`). |
| `GET` | `/security` | Renders the security information page (`security.html`). |
| `GET` | `/terms` | Renders the terms of service page (`terms.html`). |

---

### POST /analyze

**Description:** Main analysis endpoint. Accepts a resume file and a job description string, and returns an analysis including a match score, missing keywords, improvement suggestions, and predicted roles.

**Request Format:**
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes | The resume file to analyze. Supported formats: `.pdf`, `.docx`, `.txt`. Maximum size: 5MB. |
| `job_description` | String | Yes | The plain text of the job description. Must be at least 20 words. |

**Response Format (Success 200 OK):**
```json
{
  "score": 73.5,
  "score_label": "Good Match",
  "score_color": "#3B82F6",
  "missing_keywords": [
    "Python",
    "Docker",
    "Terraform"
  ],
  "jd_keywords": [
    "Python",
    "Docker",
    "Terraform",
    "AWS",
    "SQL"
  ],
  "suggestions": [
    "Add Python to your skills section",
    "Mention Docker experience in your work history"
  ],
  "resume_word_count": 412,
  "jd_word_count": 318,
  "predicted_roles": [
    {
      "role": "ENGINEERING",
      "confidence": 87.5
    },
    {
      "role": "INFORMATION-TECHNOLOGY",
      "confidence": 71.2
    },
    {
      "role": "CONSULTANT",
      "confidence": 58.0
    }
  ]
}
```

**Score Labels & Ranges:**
- `"Excellent Match"` → score >= 80
- `"Good Match"` → score >= 60
- `"Fair Match"` → score >= 40
- `"Needs Work"` → score < 40

**Error Codes:**
All error responses return a JSON object containing a human-readable message, e.g., `{"error": "Human-readable message"}`.

| Status Code | Description |
|---|---|
| `400 Bad Request` | Missing file, missing job description, or unsupported file type. |
| `413 Payload Too Large` | The uploaded file exceeds the 5MB size limit. |
| `422 Unprocessable Entity` | A supported file was uploaded, but no text could be extracted from it. |
| `500 Internal Server Error` | An unexpected error occurred on the server during processing. |

---

### POST /health

**Description:** Health check endpoint used to verify that the application and its NLP models are loaded and ready to accept requests.

**Request Format:**
- **Method:** `POST`
- **Content-Type:** Any

**Response Format (Success 200 OK):**
```json
{
  "status": "ok",
  "models_loaded": true
}
```

---

## Examples

### cURL Example for /analyze
```bash
curl -X POST http://localhost:5000/analyze \
  -F "file=@resume.pdf" \
  -F "job_description=We are looking for a Python developer with experience in Docker and AWS..."
```

### Python Requests Example for /analyze
```python
import requests

url = "http://localhost:5000/analyze"
job_description_text = "We are looking for a Python developer with experience in Docker and AWS..."

# Open the resume file in binary mode
with open("resume.pdf", "rb") as f:
    files = {
        "file": ("resume.pdf", f, "application/pdf")
    }
    data = {
        "job_description": job_description_text
    }
    
    response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    print(response.json())
else:
    print(f"Error {response.status_code}: {response.text}")
```

---

## Notes
- **Data Privacy:** Any file uploaded to the server is deleted immediately after the text has been parsed and processing is complete. No data is stored between requests.
- **Scoring Mechanism:** The score is based on semantic similarity of the text embeddings (computed via cosine similarity), not exact keyword matching.
- **Model Dependencies:** The `predicted_roles` array will be empty `[]` if the model files are not present in the `models/` directory.
