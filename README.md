# Automated Resume Parser

Extracts candidate details (name, email, phone, skills, education) from PDF or
Word resumes using spaCy (NLP), PDFPlumber/docx2txt (text extraction), Flask
(web app), and PostgreSQL (searchable storage).

## How it works

1. **PDFPlumber** / **docx2txt** pull raw text out of the uploaded file.
2. **spaCy**'s pretrained English model tags entities in the text (people,
   organizations, dates); we use this to find the candidate's name.
3. **Regular expressions** extract email and phone number (structured data
   like this is more reliable to match with patterns than NLP).
4. A predefined list of ~50 common skills (`data/skills.json`) is checked
   against the resume text to find which ones appear.
5. Lines mentioning education keywords (Bachelor, University, B.Tech, etc.)
   are extracted as the education section.
6. Everything is saved to a **PostgreSQL** table, so you can search
   candidates by skill later (e.g. "show me everyone who knows Python").

## Project structure

```
resume-parser/
├── app.py              # Flask server (run this)
├── parser.py           # Text extraction + NLP logic
├── database.py         # PostgreSQL layer
├── requirements.txt
├── .env.example         # Copy to .env and fill in your DB password
├── data/
│   └── skills.json       # Skill keywords to match against
├── uploads/               # Uploaded resumes get saved here (gitignored)
├── templates/
│   ├── index.html          # Upload form + candidate list
│   └── search.html          # Skill search results
└── static/
    └── style.css              # Styling
```

## Setup & run (local machine)

### 1. Install Python 3.12 (if you don't already have a working version)
Confirm with: `python --version`

### 2. Install PostgreSQL
Download from https://www.postgresql.org/download/ and install it. During
setup you'll be asked to set a password for the default `postgres` user -
remember it, you'll need it in step 5. Keep the default port `5432`.

### 3. Create the database
Open **pgAdmin** (installed alongside PostgreSQL) or run this in a terminal:
```
psql -U postgres
```
Then, inside the psql prompt:
```sql
CREATE DATABASE resume_parser;
\q
```

### 4. Set up a virtual environment and install dependencies
```
python -m venv venv
```
Activate it:
- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

Install packages:
```
pip install -r requirements.txt
```

Download spaCy's English language model (a one-time ~13MB download):
```
python -m spacy download en_core_web_sm
```

### 5. Configure your database credentials
Copy `.env.example` to a new file named `.env`, and fill in the password you
set during PostgreSQL installation:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=resume_parser
DB_USER=postgres
DB_PASSWORD=your_actual_password
```

### 6. Run the app
```
python app.py
```
Open `http://127.0.0.1:5000`, upload a resume, and see it parsed automatically.

## Customizing

- Add more skills by editing `data/skills.json`.
- Add more education keywords in `EDUCATION_KEYWORDS` inside `parser.py`.
- The name-extraction logic assumes the candidate's name appears in the first
  ~500 characters of the resume (true for almost all standard formats).

## Publishing to GitHub

```
git init
git add .
git commit -m "Automated resume parser with spaCy, Flask, PostgreSQL"
```
Create a new repo on GitHub, then:
```
git remote add origin https://github.com/<your-username>/resume-parser.git
git branch -M main
git push -u origin main
```

Your `.env` file (with your real database password) is already excluded via
`.gitignore`, so it will never be pushed - only `.env.example` (with no real
password) gets committed.

Then share the GitHub link plus your name to vaishali@codectechnologies.in
as required.
