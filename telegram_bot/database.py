"""
SQLite Database Layer for Telegram Username Bot
"""
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import DATABASE_PATH, DEFAULT_FREE_QUERIES, DEFAULT_PROMOCODES


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables and initial promo codes"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                is_premium INTEGER DEFAULT 0,
                queries_left INTEGER DEFAULT 2,
                total_searches INTEGER DEFAULT 0,
                registered_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS found_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                length INTEGER,
                valuation_ton INTEGER,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY,
                is_used INTEGER DEFAULT 0,
                used_by INTEGER
            )
        """)

        # Seed initial promo codes
        for code in DEFAULT_PROMOCODES:
            cursor.execute(
                "INSERT OR IGNORE INTO promocodes (code, is_used) VALUES (?, 0)",
                (code.upper(),)
            )

        conn.commit()


def get_or_create_user(user_id: int, username: Optional[str], full_name: str) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            # Update latest username or full_name if changed
            cursor.execute(
                "UPDATE users SET username = ?, full_name = ? WHERE user_id = ?",
                (username or "", full_name, user_id)
            )
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(cursor.fetchone())

        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        cursor.execute("""
            INSERT INTO users (user_id, username, full_name, is_premium, queries_left, total_searches, registered_at)
            VALUES (?, ?, ?, 0, ?, 0, ?)
        """, (user_id, username or "", full_name, DEFAULT_FREE_QUERIES, now))
        conn.commit()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return dict(cursor.fetchone())


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def can_search(user_id: int) -> bool:
    user = get_user(user_id)
    if not user:
        return False
    if user["is_premium"]:
        return True
    return user["queries_left"] > 0


def consume_search(user_id: int) -> bool:
    """Consume one search query if not premium. Returns True if consumed successfully."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_premium, queries_left, total_searches FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return False

        is_prem, queries_left, total = row["is_premium"], row["queries_left"], row["total_searches"]

        if is_prem:
            cursor.execute("UPDATE users SET total_searches = total_searches + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            return True

        if queries_left > 0:
            cursor.execute("""
                UPDATE users 
                SET queries_left = queries_left - 1, total_searches = total_searches + 1 
                WHERE user_id = ?
            """, (user_id,))
            conn.commit()
            return True

        return False


def activate_premium(user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0


def redeem_promocode(user_id: int, code: str) -> tuple[bool, str]:
    code_clean = code.strip().upper()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM promocodes WHERE code = ?", (code_clean,))
        row = cursor.fetchone()

        if not row:
            return False, "❌ Промокод не найден."

        if row["is_used"]:
            return False, "⚠️ Этот промокод уже был активирован ранее."

        # Mark promo code as used
        cursor.execute("UPDATE promocodes SET is_used = 1, used_by = ? WHERE code = ?", (user_id, code_clean))
        cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        return True, "🎉 Премиум успешно активирован! Теперь у вас безлимитный поиск."


def save_found_username(user_id: int, username: str, length: int, valuation_ton: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        cursor.execute("""
            INSERT INTO found_history (user_id, username, length, valuation_ton, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, length, valuation_ton, now))
        conn.commit()


def get_user_history(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM found_history 
            WHERE user_id = ? 
            ORDER BY id DESC 
            LIMIT ?
        """, (user_id, limit))
        return [dict(r) for r in cursor.fetchall()]
