"""Authentication module for FoodSure AI.

Uses Argon2id for secure password hashing and SQLite for persistent user storage.
Passwords are never stored in plaintext.
"""

from __future__ import annotations

import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

DB_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DB_DIR / "foodsure_auth.db"

_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

EMAIL_REGEX = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,63}$")


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


def init_auth_db() -> None:
    """Initialize the users table and seed initial demo researcher account if empty."""
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'researcher',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

        # Seed initial demo researcher account if database has 0 users
        cursor = conn.execute("SELECT COUNT(*) AS count FROM users")
        if cursor.fetchone()["count"] == 0:
            demo_id = str(uuid.uuid4())
            demo_email = "researcher@foodsure.ai"
            demo_pw = "FoodSure2026!"
            demo_hash = _HASHER.hash(demo_pw)
            created_at = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO users (user_id, email, password_hash, full_name, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (demo_id, demo_email, demo_hash, "Dr. Food Science Researcher", "lead_researcher", created_at),
            )
            conn.commit()


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email or len(email) > 254:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength. Minimum 8 chars with digit/letter mix."""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password must be at most 128 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    return True, ""


def register_user(
    email: str,
    password: str,
    full_name: str,
    role: str = "researcher",
) -> tuple[bool, str, dict[str, Any] | None]:
    """Register a new user with Argon2id hashed password."""
    init_auth_db()

    email_clean = email.strip().lower()
    name_clean = full_name.strip()

    if not name_clean:
        return False, "Full name is required.", None
    if not validate_email(email_clean):
        return False, "Invalid email address format.", None

    is_valid_pw, pw_err = validate_password(password)
    if not is_valid_pw:
        return False, pw_err, None

    user_id = str(uuid.uuid4())
    pw_hash = _HASHER.hash(password)
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, email, password_hash, full_name, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, email_clean, pw_hash, name_clean, role, now_iso),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return False, "An account with this email address already exists.", None
    except Exception as exc:
        return False, f"Registration failed due to a database error: {type(exc).__name__}", None

    user_info = {
        "user_id": user_id,
        "email": email_clean,
        "full_name": name_clean,
        "role": role,
        "created_at": now_iso,
    }
    return True, "Registration successful.", user_info


def authenticate_user(
    email: str,
    password: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Authenticate user with email and password using Argon2id verification."""
    init_auth_db()

    email_clean = email.strip().lower()
    if not email_clean or not password:
        return False, "Email and password are required.", None

    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                "SELECT user_id, email, password_hash, full_name, role, created_at FROM users WHERE email = ?",
                (email_clean,),
            )
            row = cursor.fetchone()
    except Exception as exc:
        return False, f"Authentication error: {type(exc).__name__}", None

    if not row:
        return False, "Invalid email or password.", None

    pw_hash = row["password_hash"]
    try:
        _HASHER.verify(pw_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False, "Invalid email or password.", None
    except Exception:
        return False, "Authentication service error. Please try again.", None

    # Check if hash needs rehash (e.g. if argon2 parameters were updated)
    if _HASHER.check_needs_rehash(pw_hash):
        try:
            new_hash = _HASHER.hash(password)
            with _get_connection() as conn:
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE user_id = ?",
                    (new_hash, row["user_id"]),
                )
                conn.commit()
        except Exception:
            pass

    user_info = {
        "user_id": row["user_id"],
        "email": row["email"],
        "full_name": row["full_name"],
        "role": row["role"],
        "created_at": row["created_at"],
    }
    return True, "Authentication successful.", user_info


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    """Fetch user profile without sensitive password hash."""
    init_auth_db()
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                "SELECT user_id, email, full_name, role, created_at FROM users WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
    except Exception:
        pass
    return None
