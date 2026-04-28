"""
B.13: Дедупликация откликов через SQLite.

Предотвращает повторный отклик на вакансию и считает дневной лимит.
"""

import logging
import os
import sqlite3
from datetime import date, datetime

from src.config import BASE_DIR

logger = logging.getLogger(__name__)

DB_PATH = BASE_DIR / ".applied.db"

MAX_APPLIES_PER_DAY = int(os.getenv("MAX_APPLIES_PER_DAY", "20"))


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applied (
                vacancy_id TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL,
                title TEXT,
                company TEXT,
                letter_attached INTEGER DEFAULT 0
            )
        """)


def is_applied(vacancy_id: str) -> bool:
    if not DB_PATH.exists():
        return False
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT 1 FROM applied WHERE vacancy_id = ?", (vacancy_id,)
        ).fetchone()
        return row is not None


def mark_applied(vacancy_id: str, title: str = "", company: str = "", letter: bool = False):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO applied (vacancy_id, applied_at, title, company, letter_attached) "
            "VALUES (?, ?, ?, ?, ?)",
            (vacancy_id, datetime.now().isoformat(), title, company, int(letter)),
        )


def get_applied_count_today() -> int:
    if not DB_PATH.exists():
        return 0
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM applied WHERE applied_at LIKE ?", (f"{today}%",)
        ).fetchone()
        return row[0] if row else 0


def check_daily_limit() -> bool:
    return get_applied_count_today() < MAX_APPLIES_PER_DAY
