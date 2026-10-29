"""Analysis history persistence module for FoodSure AI.

Stores analysis runs securely with strict user isolation in SQLite.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

DB_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DB_DIR / "foodsure_history.db"


@contextmanager
def _get_connection() -> Generator[sqlite3.Connection, None, None]:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_history_db() -> None:
    """Initialize analysis history table with index on user_id."""
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                analysis_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sample_id TEXT NOT NULL,
                input_source TEXT NOT NULL,
                modality TEXT NOT NULL,
                predicted_class TEXT NOT NULL,
                predicted_percentage REAL,
                actual_level REAL,
                status TEXT NOT NULL,
                confidence_note TEXT,
                analysis_mode TEXT NOT NULL,
                summary TEXT,
                report_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_history_user_id ON analysis_history(user_id, timestamp DESC)"
        )
        conn.commit()


def save_analysis(
    user_id: str,
    sample_id: str,
    input_source: str,
    modality: str,
    predicted_class: str,
    predicted_percentage: float | None,
    actual_level: float | None,
    status: str,
    confidence_note: str,
    analysis_mode: str,
    summary: str,
    full_report: dict[str, Any],
) -> str:
    """Save an analysis record under the user's account."""
    init_history_db()
    analysis_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    report_serialized = json.dumps(full_report, ensure_ascii=False)

    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO analysis_history (
                analysis_id, user_id, timestamp, sample_id, input_source,
                modality, predicted_class, predicted_percentage, actual_level,
                status, confidence_note, analysis_mode, summary, report_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_id,
                user_id,
                now_iso,
                sample_id,
                input_source,
                modality,
                predicted_class,
                predicted_percentage,
                actual_level,
                status,
                confidence_note,
                analysis_mode,
                summary,
                report_serialized,
            ),
        )
        conn.commit()
    return analysis_id


def get_user_history(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Retrieve history for a specific user only, enforcing user isolation."""
    init_history_db()
    results: list[dict[str, Any]] = []
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT analysis_id, timestamp, sample_id, input_source, modality,
                       predicted_class, predicted_percentage, actual_level, status,
                       confidence_note, analysis_mode, summary
                FROM analysis_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            for row in cursor.fetchall():
                results.append(dict(row))
    except Exception:
        pass
    return results


def get_analysis_by_id(analysis_id: str, user_id: str) -> dict[str, Any] | None:
    """Retrieve a single analysis record verifying user ownership."""
    init_history_db()
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM analysis_history
                WHERE analysis_id = ? AND user_id = ?
                """,
                (analysis_id, user_id),
            )
            row = cursor.fetchone()
            if row:
                data = dict(row)
                try:
                    data["report_json"] = json.loads(data["report_json"])
                except Exception:
                    pass
                return data
    except Exception:
        pass
    return None


def delete_analysis(analysis_id: str, user_id: str) -> bool:
    """Delete a specific analysis record belonging to the user."""
    init_history_db()
    with _get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM analysis_history WHERE analysis_id = ? AND user_id = ?",
            (analysis_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def clear_user_history(user_id: str) -> bool:
    """Delete all history for a specific user."""
    init_history_db()
    with _get_connection() as conn:
        conn.execute("DELETE FROM analysis_history WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
