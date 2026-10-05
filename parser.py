"""
parser.py
---------
The "brain" of the resume parser.

How it works (in plain English):
1. TEXT EXTRACTION: depending on the file type, we pull raw text out of the
   resume. PDFPlumber reads PDFs page by page; docx2txt reads Word files.
2. NAME EXTRACTION: we run the text through spaCy's pretrained NLP model,
   which tags words with labels like PERSON, ORG, DATE, etc. (this is called
   Named Entity Recognition, or NER). We assume the first PERSON entity
   found near the top of the resume is the candidate's name.
3. EMAIL / PHONE: these have a predictable shape, so we use regular
   expressions (pattern matching) rather than NLP - it's more reliable for
   structured data like this.
4. SKILLS: we keep a list of ~50 common tech/soft skills (data/skills.json)
   and check which of them appear anywhere in the resume text (case
   insensitive). This is simple but effective for structured skill sections.
5. EDUCATION: we scan line by line for education-related keywords (Bachelor,
   Master, B.Tech, University, College, etc.) and return matching lines.

The result is a dictionary with name, email, phone, skills, and education -
ready to store in the database or show on the results page.
"""

import re
import json
import os

import spacy
import pdfplumber
import docx2txt

# Load spaCy's small English model once when this module is imported
# (loading it is somewhat slow, so we don't want to do it per-request)
nlp = spacy.load("en_core_web_sm")

SKILLS_PATH = os.path.join(os.path.dirname(__file__), "data", "skills.json")
with open(SKILLS_PATH, "r", encoding="utf-8") as f:
    SKILL_LIST = json.load(f)["skills"]

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}")

EDUCATION_KEYWORDS = [
    "bachelor", "master", "b.tech", "m.tech", "b.sc", "m.sc", "bca", "mca",
    "phd", "doctorate", "university", "college", "institute of technology",
    "diploma", "high school", "secondary school",
]


def extract_text_from_pdf(file_path: str) -> str:
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(file_path: str) -> str:
    return docx2txt.process(file_path) or ""


def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def extract_name(text: str) -> str:
    """Assume the candidate's name is the first PERSON entity spaCy finds,
    searched within roughly the first 500 characters (names are almost
    always at the very top of a resume)."""
    snippet = text[:500]
    doc = nlp(snippet)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()
    return "Not found"


def extract_email(text: str) -> str:
    match = EMAIL_REGEX.search(text)
    return match.group(0) if match else "Not found"


def extract_phone(text: str) -> str:
    for match in PHONE_REGEX.finditer(text):
        candidate = match.group(0)
        digit_count = sum(c.isdigit() for c in candidate)
        # Require at least 7 digits so we don't match dates, zip codes, etc.
        if digit_count >= 7:
            return candidate.strip()
    return "Not found"


def extract_skills(text: str) -> list:
    text_lower = text.lower()
    found = []
    for skill in SKILL_LIST:
        # Word-boundary match so "Go" doesn't match inside "Google"
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def extract_education(text: str) -> list:
    lines = text.split("\n")
    matches = []
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in EDUCATION_KEYWORDS):
            cleaned = line.strip()
            if cleaned and cleaned not in matches:
                matches.append(cleaned)
    return matches


def parse_resume(file_path: str) -> dict:
    """Main entry point: takes a file path, returns structured candidate data."""
    text = extract_text(file_path)

    if not text.strip():
        raise ValueError("Could not extract any text from this file. It may be a scanned image PDF without a text layer.")

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "raw_text": text,
    }
