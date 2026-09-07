import sqlite3
from contextlib import closing
from pathlib import Path

# Keep the database in the project folder, regardless of the working directory.
DATABASE_PATH = Path(__file__).resolve().parent.parent / "tickets.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    # Rows can be accessed by column name, including from Jinja2 templates.
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with closing(get_connection()) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_assessments (
                id INTEGER PRIMARY KEY,
                ticket_id INTEGER NOT NULL UNIQUE REFERENCES tickets(id),
                category TEXT NOT NULL CHECK (category IN ('Network', 'Hardware', 'Software', 'Account Access', 'Security', 'Other')),
                priority TEXT NOT NULL CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
                summary TEXT NOT NULL,
                recommended_team TEXT NOT NULL CHECK (length(trim(recommended_team)) > 0),
                requires_human_review INTEGER NOT NULL CHECK (requires_human_review IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS human_reviews (
                id INTEGER PRIMARY KEY,
                assessment_id INTEGER NOT NULL UNIQUE REFERENCES ai_assessments(id),
                decision TEXT NOT NULL CHECK (decision IN ('approved', 'modified')),
                category TEXT NOT NULL CHECK (category IN ('Network', 'Hardware', 'Software', 'Account Access', 'Security', 'Other')),
                priority TEXT NOT NULL CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
                team TEXT NOT NULL CHECK (length(trim(team)) > 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def create_ticket(title: str, description: str) -> int:
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "INSERT INTO tickets (title, description) VALUES (?, ?)",
            (title, description),
        )
        connection.commit()
        return cursor.lastrowid


def list_tickets():
    with closing(get_connection()) as connection:
        return connection.execute(
            "SELECT id, title, created_at FROM tickets ORDER BY created_at DESC, id DESC"
        ).fetchall()


def get_ticket(ticket_id: int):
    with closing(get_connection()) as connection:
        return connection.execute(
            "SELECT id, title, description, created_at FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()


def save_assessment(ticket_id: int, assessment: dict):
    with closing(get_connection()) as connection:
        # A repeated click keeps the original assessment, even after review.
        connection.execute(
            """
            INSERT INTO ai_assessments
                (ticket_id, category, priority, summary, recommended_team, requires_human_review)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticket_id) DO NOTHING
            """,
            (
                ticket_id,
                assessment["category"],
                assessment["priority"],
                assessment["summary"],
                assessment["recommended_team"],
                assessment["requires_human_review"],
            ),
        )
        connection.commit()


def get_assessment(ticket_id: int):
    with closing(get_connection()) as connection:
        return connection.execute(
            "SELECT * FROM ai_assessments WHERE ticket_id = ?", (ticket_id,)
        ).fetchone()


def save_review(assessment_id: int, decision: str, category: str, priority: str, team: str):
    with closing(get_connection()) as connection:
        # The first final decision is kept if the form is submitted twice.
        connection.execute(
            """
            INSERT INTO human_reviews (assessment_id, decision, category, priority, team)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(assessment_id) DO NOTHING
            """,
            (assessment_id, decision, category, priority, team),
        )
        connection.commit()


def get_review(assessment_id: int):
    with closing(get_connection()) as connection:
        return connection.execute(
            "SELECT * FROM human_reviews WHERE assessment_id = ?", (assessment_id,)
        ).fetchone()
