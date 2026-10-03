# ResumeFit AI API Documentation

## Overview
The ResumeFit AI API provides developers with access to a lightweight, AI-powered backend for analyzing how well a resume matches a given job description. It uses NLP techniques and the `all-MiniLM-L6-v2` SBERT model to compute semantic similarity scores, extract missing keywords, provide actionable suggestions, and predict likely job roles based on the resume content. Signed-in users can also keep a history of their analyses and track how their score changes over time.

## Base URL
All API requests should be prefixed with the base URL of your local deployment:
```text
http://localhost:5000
```

## Authentication
Analysis works for everyone, with limits that depend on who is calling:

| Caller | Limit | History saved |
|---|---|---|
| **Guest** (no sign-in) | 2 successful analyses per browser session | No |
| **Signed-in** (Google) | Unlimited | Yes |

- Sign-in uses Google OAuth 2.0 (OpenID Connect). Open `/login` in a browser to start it. A successful sign-in sets a signed session cookie.
- Authenticated endpoints read that cookie. Clients such as `curl` or `requests` must send the cookie to be treated as signed in.
- The guest counter is stored in the session cookie, so it is a soft limit. Clearing cookies resets it.
- Endpoints under `/api/` that require sign-in return `401` with `{"error": "Login required.", "login_required": true}` when the caller is not signed in. Page routes such as `/dashboard` redirect to `/login` instead.

## Rate Limiting
Apart from the guest limit above, there is no rate limiting on this local deployment. Since the NLP models run on the CPU, it is recommended to limit concurrent requests to avoid performance degradation.

---

## Endpoints

### Page Endpoints
The following endpoints serve HTML pages or handle the sign-in flow.

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | No | Renders the main user interface (`index.html`). |
| `GET` | `/docs` | No | Renders the documentation and FAQ page (`docs.html`). Note: `/help` redirects here. |
| `GET` | `/privacy` | No | Renders the privacy policy page (`privacy.html`). |
| `GET` | `/security` | No | Renders the security information page (`security.html`). |
| `GET` | `/terms` | No | Renders the terms of service page (`terms.html`). |
| `GET` | `/login` | No | Starts Google sign-in by redirecting to Google. |
| `GET` | `/auth/callback` | No | Google redirects here after sign-in. Creates the user on first sign-in, then redirects to `/dashboard`. |
| `GET` | `/logout` | No | Signs the user out and redirects to `/`. |
| `GET` | `/dashboard` | Yes | Renders the progress dashboard (`dashboard.html`). Redirects to `/login` if not signed in. |

---

### POST /analyze

**Description:** Main analysis endpoint. Accepts a resume file and a job description string, and returns an analysis including a match score, missing keywords, improvement suggestions, and predicted roles. For signed-in users the result is also saved to their history.

**Request Format:**
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes* | The resume file to analyze. Supported formats: `.pdf`, `.docx`, `.txt`. Maximum size: 5MB. |
| `resume_text` | String | Yes* | Plain resume text, used instead of `file`. *Provide either `file` or `resume_text`. |
| `job_description` | String | Yes | The plain text of the job description. Must be at least 20 words. |
| `resume_label` | String | No | A name for this resume, for example `Backend CV`. Used to group analyses on the dashboard. Defaults to `My resume`. Maximum 120 characters. Ignored for guests. |
| `jd_title` | String | No | The target job title. Maximum 200 characters. Ignored for guests. |

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
  ],
  "resume_text": "Extracted resume text...",
  "saved": true,
  "guest_uses_left": null
}
```

| Field | Description |
|---|---|
| `resume_text` | The text extracted from the resume, returned so the page can display it. It is not stored. |
| `saved` | `true` if the result was saved to a signed-in user's history, otherwise `false`. |
| `guest_uses_left` | For guests, the number of free analyses remaining (`1` or `0`). `null` for signed-in users. |

**Score Labels & Ranges:**
- `"Excellent Match"` → score >= 80
- `"Good Match"` → score >= 60
- `"Fair Match"` → score >= 40
- `"Needs Work"` → score < 40

**Error Codes:**
All error responses return a JSON object containing a human-readable message, e.g., `{"error": "Human-readable message"}`.

| Status Code | Description |
|---|---|
| `400 Bad Request` | Missing file or text, missing job description, job description under 20 words, or unsupported file type. |
| `403 Forbidden` | A guest has used both free analyses. The body also contains `"login_required": true`. |
| `413 Payload Too Large` | The uploaded file exceeds the 5MB size limit. |
| `422 Unprocessable Entity` | A supported file was uploaded, but no text could be extracted from it. |
| `500 Internal Server Error` | An unexpected error occurred on the server during processing. |

---

### POST /reanalyze

**Description:** Re-runs the analysis on text you supply, without uploading a file again. It follows the same guest limit and saving rules as `/analyze`.

**Request Format:**
- **Method:** `POST`
- **Content-Type:** `application/json`

| Field | Type | Required | Description |
|---|---|---|---|
| `resume_text` | String | Yes | The resume text. Must be at least 50 characters. |
| `job_description` | String | Yes | The job description. Must be at least 20 words. |
| `resume_label` | String | No | Resume name, as in `/analyze`. |
| `jd_title` | String | No | Target job title, as in `/analyze`. |

**Response Format:** the same as `/analyze`.

**Error Codes:** `400` for a missing or too-short field, `403` when a guest has reached the limit.

---

### GET /api/history

**Auth:** Required.

**Description:** Returns the signed-in user's saved analyses and per-resume progress, oldest first.

**Response Format (Success 200 OK):**
```json
{
  "total": 2,
  "average_score": 45.4,
  "best_score": 52.6,
  "analyses": [
    {
      "id": 1,
      "label": "Backend CV",
      "jd_title": "Backend Developer",
      "score": 38.2,
      "missing_count": 12,
      "created_at": "2026-10-03T06:09:00.564594Z"
    },
    {
      "id": 2,
      "label": "Backend CV",
      "jd_title": "Backend Developer",
      "score": 52.6,
      "missing_count": 8,
      "created_at": "2026-10-05T09:30:12.100000Z"
    }
  ],
  "progress": [
    {
      "label": "Backend CV",
      "count": 2,
      "first_score": 38.2,
      "latest_score": 52.6,
      "improvement": 14.4
    }
  ]
}
```

`progress` groups analyses by `label`. `improvement` is the latest score minus the first score for that label.

**Error Codes:** `401` if not signed in.

---

### DELETE /api/analysis/{id}

**Auth:** Required.

**Description:** Deletes one saved analysis. A user can delete only their own records.

**Response Format (Success 200 OK):**
```json
{ "ok": true }
```

**Error Codes:** `401` if not signed in. `404` if the analysis does not exist or belongs to another user.

---

### DELETE /api/account

**Auth:** Required.

**Description:** Permanently deletes the signed-in user's account and all of their saved analyses, and signs them out.

**Response Format (Success 200 OK):**
```json
{ "ok": true }
```

**Error Codes:** `401` if not signed in.

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

### cURL Example for /analyze (guest)
```bash
curl -X POST http://localhost:5000/analyze \
  -F "file=@resume.pdf" \
  -F "job_description=We are looking for a Python developer with experience in Docker and AWS..."
```
Each call without a cookie counts as a new guest. To see the limit in action, store and send cookies with `-c cookies.txt -b cookies.txt`.

### Python Requests Example for /analyze
```python
import requests

url = "http://localhost:5000/analyze"
job_description_text = "We are looking for a Python developer with experience in Docker and AWS..."

# A Session keeps cookies between calls, so the guest limit applies as in a browser
session = requests.Session()

# Open the resume file in binary mode
with open("resume.pdf", "rb") as f:
    files = {
        "file": ("resume.pdf", f, "application/pdf")
    }
    data = {
        "job_description": job_description_text
    }

    response = session.post(url, files=files, data=data)

if response.status_code == 200:
    print(response.json())
else:
    print(f"Error {response.status_code}: {response.text}")
```

---

## Notes
- **Data Privacy:** An uploaded file is written to a temporary location only long enough to extract its text, then deleted. Resume text and job descriptions are never stored. For signed-in users, only the resume name, job title, score, missing keywords, predicted roles, and timestamp are saved. Users can delete a single analysis or their entire account at any time.
- **Scoring Mechanism:** The score is based on semantic similarity of the text embeddings (computed via cosine similarity), not exact keyword matching.
- **Model Dependencies:** The `predicted_roles` array will be empty `[]` if the model files are not present in the `models/` directory.
- **Configuration:** Sign-in requires `SECRET_KEY`, `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in the `.env` file. See the README for setup.