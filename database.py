"""
database.py
-----------
Handles all PostgreSQL interaction. Connection details come from environment
variables (loaded from a .env file) rather than being hardcoded, so you never
commit real credentials to GitHub.

Unlike SQLite, PostgreSQL needs a running server - see README.md for how to
install it and create the database this file expects.
"""

import os
import json
from datetime import datetime

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()  # reads variables from a .env file into the environment

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "resume_parser"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    """Create the candidates table if it doesn't already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS candidates (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            skills JSONB,
            education JSONB,
            raw_text TEXT,
            filename TEXT,
            uploaded_at TIMESTAMP
        )
        """
    )
    conn.commit()
    cursor.close()
    conn.close()


def save_candidate(data: dict, filename: str) -> int:
    """Insert a parsed candidate record. Returns the new row's id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO candidates (name, email, phone, skills, education, raw_text, filename, uploaded_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            data["name"],
            data["email"],
            data["phone"],
            json.dumps(data["skills"]),
            json.dumps(data["education"]),
            data["raw_text"],
            filename,
            datetime.utcnow(),
        ),
    )
    new_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return new_id


def get_all_candidates() -> list:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT id, name, email, phone, skills, education, filename, uploaded_at "
        "FROM candidates ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(row) for row in rows]


def search_by_skill(skill: str) -> list:
    """Find candidates whose skills list contains the given skill (case-insensitive)."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        """
        SELECT id, name, email, phone, skills, education, filename, uploaded_at
        FROM candidates
        WHERE EXISTS (
            SELECT 1 FROM jsonb_array_elements_text(skills) AS s
            WHERE LOWER(s) = LOWER(%s)
        )
        ORDER BY id DESC
        """,
        (skill,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(row) for row in rows]
