import sqlite3
from contextlib import closing
from pathlib import Path

# Keep the database in the project folder, regardless of the working directory.
DATABASE_PATH = Path(__file__).resolve().parent.parent / "tickets.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    # Rows can be accessed by column name, including from Jinja2 templates.
    connection.row_factory = sqlite3.Row
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
