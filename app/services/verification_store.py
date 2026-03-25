"""
SQLite-based verification persistence.
Stores recent verification results for the dashboard feed.
"""

import sqlite3
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger("verifier")

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "verifications.db")


def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT NOT NULL,
            trust_score REAL NOT NULL,
            mode TEXT NOT NULL DEFAULT 'full',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"Verification store initialized at {DB_PATH}")


def save_verification(input_text: str, trust_score: float, mode: str = "full"):
    """Save a verification result to the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO verifications (input_text, trust_score, mode, created_at) VALUES (?, ?, ?, ?)",
            (input_text[:500], round(trust_score, 3), mode, datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Failed to save verification: {e}")


def get_recent_verifications(limit: int = 10) -> list[dict]:
    """Retrieve the most recent verifications."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, input_text, trust_score, mode, created_at FROM verifications ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.warning(f"Failed to fetch recent verifications: {e}")
        return []
