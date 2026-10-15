# ResumeLens — AI-Powered Resume Analyzer

Upload a PDF/DOCX resume + paste a job description → transparent score, skills gap, ATS checks, actionable feedback, downloadable report.

## How each module works
- `analyzer/resume_parser.py` — validates file, extracts text (PyMuPDF → pdfplumber fallback for PDF, python-docx for DOCX), detects 8 sections via heading heuristics, runs 7 ATS readability checks.
- `analyzer/skill_extractor.py` — curated skill list (~70 skills) matched with regex + top keyword extraction with stopword filtering.
- `analyzer/job_matcher.py` — set comparison resume vs JD → matched/missing skills & keywords + coverage ratios.
- `analyzer/scoring.py` — weighted score: Skills 35%, Experience/Projects 25%, Keywords 20%, Structure 10%, Education 10%. Includes disclaimer (not an ATS predictor).
- `analyzer/feedback.py` — rule-based strengths/improvements/suggestions; optionally enhanced by OpenAI-compatible LLM if `OPENAI_API_KEY` set. Never advises lying.
- `app.py` — Flask routes `/` and `/api/analyze` (JSON). Temp-file uploads deleted after processing. 5 MB limit. No resume contents logged.

## Setup (Windows PowerShell)
```powershell
cd "c:\Users\aryan\OneDrive\Desktop\ai based resume"
python -m venv venv; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python app.py
# open http://127.0.0.1:5000
```

## Optional AI
Set in `.env`:
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```
Without a key the app fully works rule-based (badge shows "Rule-based").

## Sample test
1. Create a small DOCX/PDF resume with sections: Contact (email/phone), Summary, Education, Skills (Python, SQL, Git), Experience (internship with dates + bullets), Projects.
2. Click "Load sample" for the JD, upload resume, click Analyze.
3. Expect: score 0–100 with breakdown, matched skills (python/sql/git...), missing (flask/docker/aws...), ATS checks, downloadable report.

## Sample API output
```json
{"scores":{"total":62.5,"breakdown":{"skills_match":50.0,"experience_projects":70.0,"keyword_match":40.0,"structure":80.0,"education_certs":75.0}},"match":{"matched_skills":["python","sql"],"missing_skills":["flask","docker"]}}
```

## Troubleshooting
- `Could not extract text` → PDF is scanned images; export text-based PDF/DOCX.
- 413 File too large → keep under 5 MB (raise MAX_UPLOAD_MB in .env).
- pip install fails for PyMuPDF → `pip install --upgrade pip` then retry; Windows wheels exist for Python 3.9–3.12.
- Port in use → `python app.py` uses 5000; change port in app.py if needed.
- API key errors → app auto-falls back to rule-based; check OPENAI_BASE_URL/MODEL.
