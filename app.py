"""
app.py
------
The web server. Run this with: python app.py
Then open: http://127.0.0.1:5000

Routes:
  GET  /            -> upload form + list of all parsed candidates
  POST /upload       -> handles a resume upload, parses it, saves to DB
  GET  /search        -> search candidates by a skill (?skill=Python)
"""

import os
import uuid

from flask import Flask, render_template, request, redirect, url_for, flash

import database
from parser import parse_resume

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-this-in-production"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create the candidates table if this is the first run.
# If PostgreSQL isn't reachable, we let the app still start so the upload
# page loads, but uploads will fail with a clear error until the DB is set up.
try:
    database.init_db()
except Exception as e:
    print(f"[WARNING] Could not connect to PostgreSQL on startup: {e}")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    try:
        candidates = database.get_all_candidates()
    except Exception as e:
        candidates = []
        flash(f"Could not load candidates from the database: {e}", "error")
    return render_template("index.html", candidates=candidates)


@app.route("/upload", methods=["POST"])
def upload():
    if "resume" not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for("home"))

    file = request.files["resume"]

    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("home"))

    if not allowed_file(file.filename):
        flash("Only PDF and Word (.docx) files are supported.", "error")
        return redirect(url_for("home"))

    # Save with a unique name so two people uploading "resume.pdf" don't collide
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(save_path)

    try:
        parsed = parse_resume(save_path)
        database.save_candidate(parsed, filename=file.filename)
        flash(f"Parsed and saved: {parsed['name']}", "success")
    except Exception as e:
        flash(f"Failed to parse resume: {e}", "error")

    return redirect(url_for("home"))


@app.route("/search")
def search():
    skill = request.args.get("skill", "").strip()
    results = []
    if skill:
        try:
            results = database.search_by_skill(skill)
        except Exception as e:
            flash(f"Search failed: {e}", "error")
    return render_template("search.html", results=results, skill=skill)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
