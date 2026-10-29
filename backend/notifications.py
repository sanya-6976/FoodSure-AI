"""Persistent, user-isolated notification subsystem for FoodSure AI.

Tracks sample screening events, system alerts, report readiness, and daily insights.
Stored securely in SQLite with guaranteed user isolation.
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

DB_PATH = Path(__file__).resolve().parent / "data" / "foodsure.db"


def _ensure_db_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Provide a thread-safe managed connection to the notifications DB."""
    _ensure_db_dir()
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_notifications_db() -> None:
    """Create notifications table and indices if they do not exist."""
    _ensure_db_dir()
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'info',
                created_at TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                action_link TEXT,
                dedupe_key TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_notif_user_read 
            ON notifications (user_id, is_read, created_at DESC)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_notif_dedupe
            ON notifications (user_id, dedupe_key)
            """
        )
        conn.commit()


def add_notification(
    user_id: str,
    title: str,
    message: str,
    category: str = "info",
    action_link: str | None = None,
    dedupe_key: str | None = None,
) -> str | None:
    """Add a new in-app notification for the user.

    If dedupe_key is provided and already exists for this user, returns existing ID
    to ensure idempotency across Streamlit reruns.
    """
    init_notifications_db()
    with get_db_connection() as conn:
        if dedupe_key:
            cur = conn.execute(
                "SELECT id FROM notifications WHERE user_id = ? AND dedupe_key = ?",
                (user_id, dedupe_key),
            )
            row = cur.fetchone()
            if row:
                return row["id"]

        notif_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO notifications (id, user_id, title, message, category, created_at, is_read, action_link, dedupe_key)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (notif_id, user_id, title, message, category, now, action_link, dedupe_key),
        )
        conn.commit()
        return notif_id


def get_user_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Retrieve notifications isolated to the given user."""
    init_notifications_db()
    with get_db_connection() as conn:
        if unread_only:
            query = """
                SELECT * FROM notifications
                WHERE user_id = ? AND is_read = 0
                ORDER BY created_at DESC LIMIT ?
            """
            params: tuple[Any, ...] = (user_id, limit)
        else:
            query = """
                SELECT * FROM notifications
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            """
            params = (user_id, limit)

        cur = conn.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def get_unread_count(user_id: str) -> int:
    """Return count of unread notifications for navbar badge."""
    init_notifications_db()
    with get_db_connection() as conn:
        cur = conn.execute(
            "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = ? AND is_read = 0",
            (user_id,),
        )
        row = cur.fetchone()
        return int(row["cnt"]) if row else 0


def mark_as_read(notification_id: str, user_id: str) -> bool:
    """Mark a single notification as read, respecting user ownership."""
    init_notifications_db()
    with get_db_connection() as conn:
        cur = conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
            (notification_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0


def mark_all_as_read(user_id: str) -> int:
    """Mark all unread notifications as read for the user."""
    init_notifications_db()
    with get_db_connection() as conn:
        cur = conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
            (user_id,),
        )
        conn.commit()
        return cur.rowcount


def delete_notification(notification_id: str, user_id: str) -> bool:
    """Delete a single notification, respecting user ownership."""
    init_notifications_db()
    with get_db_connection() as conn:
        cur = conn.execute(
            "DELETE FROM notifications WHERE id = ? AND user_id = ?",
            (notification_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0


def clear_user_notifications(user_id: str) -> int:
    """Clear all notifications for a specific user."""
    init_notifications_db()
    with get_db_connection() as conn:
        cur = conn.execute(
            "DELETE FROM notifications WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
        return cur.rowcount
