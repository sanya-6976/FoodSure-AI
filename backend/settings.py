"""Persistent user settings & preferences subsystem for FoodSure AI.

Stores UI language, explanation depth, notification subscriptions, and display options.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

DB_PATH = Path(__file__).resolve().parent / "data" / "foodsure.db"

DEFAULT_SETTINGS: dict[str, Any] = {
    "language": "en",
    "explanation_depth": "detailed",
    "explanation_lang": "en",
    "notify_analysis": 1,
    "notify_insights": 1,
    "theme": "light",
}


def _ensure_db_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Provide a thread-safe managed connection to the settings DB."""
    _ensure_db_dir()
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_settings_db() -> None:
    """Create settings table if not already present."""
    _ensure_db_dir()
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                language TEXT NOT NULL DEFAULT 'en',
                explanation_depth TEXT NOT NULL DEFAULT 'detailed',
                explanation_lang TEXT NOT NULL DEFAULT 'en',
                notify_analysis INTEGER NOT NULL DEFAULT 1,
                notify_insights INTEGER NOT NULL DEFAULT 1,
                theme TEXT NOT NULL DEFAULT 'light',
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def get_user_settings(user_id: str) -> dict[str, Any]:
    """Retrieve settings for a user, returning defaults if not yet configured."""
    init_settings_db()
    with get_db_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM user_settings WHERE user_id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            res = dict(DEFAULT_SETTINGS)
            res["user_id"] = user_id
            return res

        data = dict(row)
        # Ensure all default keys exist
        for k, v in DEFAULT_SETTINGS.items():
            if k not in data:
                data[k] = v
        return data


def save_user_settings(user_id: str, settings: dict[str, Any]) -> bool:
    """Persist settings for a user."""
    init_settings_db()
    now = datetime.now(timezone.utc).isoformat()
    lang = settings.get("language", "en")
    depth = settings.get("explanation_depth", "detailed")
    exp_lang = settings.get("explanation_lang", "en")
    n_analysis = 1 if settings.get("notify_analysis", 1) else 0
    n_insights = 1 if settings.get("notify_insights", 1) else 0
    theme = settings.get("theme", "light")

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_settings (user_id, language, explanation_depth, explanation_lang, notify_analysis, notify_insights, theme, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                language = excluded.language,
                explanation_depth = excluded.explanation_depth,
                explanation_lang = excluded.explanation_lang,
                notify_analysis = excluded.notify_analysis,
                notify_insights = excluded.notify_insights,
                theme = excluded.theme,
                updated_at = excluded.updated_at
            """,
            (user_id, lang, depth, exp_lang, n_analysis, n_insights, theme, now),
        )
        conn.commit()
        return True
