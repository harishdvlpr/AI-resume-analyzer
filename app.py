"""AI-Powered Resume Analyzer — Flask backend."""
import os
import uuid
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from analyzer.resume_parser import validate_file, extract_text, identify_sections, ats_checks
from analyzer.job_matcher import compare
from analyzer.scoring import calculate
from analyzer.feedback import generate

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        if "resume" not in request.files:
            return jsonify({"error": "No resume file uploaded. Please choose a PDF or DOCX."}), 400
        f = request.files["resume"]
        jd_text = (request.form.get("job_description") or "").strip()
        if not f or not f.filename:
            return jsonify({"error": "No file selected."}), 400
        if not jd_text or len(jd_text) < 30:
            return jsonify({"error": "Please paste a job description (at least ~30 characters)."}), 400

        # validate via content-length if available
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0)
        ok, msg = validate_file(f.filename, size, MAX_MB)
        if not ok:
            return jsonify({"error": msg}), 400

        fname = secure_filename(f.filename)
        tmp = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{fname}")
        f.save(tmp)
        try:
            resume_text = extract_text(tmp)
        finally:
            try:
                os.remove(tmp)  # temp only, never persist
            except Exception:
                pass

        if not resume_text or len(resume_text.strip()) < 50:
            return jsonify({"error": "Could not extract text. If your PDF is scanned/images, export a text-based PDF or DOCX and retry."}), 422

        # Cap lengths to avoid abuse
        resume_text = resume_text[:30000]
        jd_text = jd_text[:20000]

        sections = identify_sections(resume_text)
        checks = ats_checks(resume_text, sections)
        match = compare(resume_text, jd_text)
        scores = calculate(match, sections, resume_text, checks)
        feedback = generate(resume_text, jd_text, sections, match, scores, checks)

        return jsonify({
            "scores": scores,
            "match": match,
            "sections_found": sorted(sections.keys()),
            "sections_missing": sorted(set(["contact","summary","education","skills","experience","projects","certifications","achievements"]) - set(sections.keys())),
            "ats_checks": checks,
            "feedback": feedback,
            "meta": {"resume_chars": len(resume_text), "resume_words": len(resume_text.split())},
        })
    except Exception as e:
        # never log resume contents; generic message
        return jsonify({"error": f"Analysis failed: {str(e)[:300]}"}), 500


@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": f"File too large. Max {MAX_MB} MB."}), 413


if __name__ == "__main__":
    app.run(debug=True, port=5000)
