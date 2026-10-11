"""
SQLite database for user settings, AFK states, stars balance, and autoresponders
"""
import sqlite3
import datetime
from typing import Optional, Dict, Any, List
from config import DB_PATH, DEFAULT_STARS


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                stars INTEGER DEFAULT 100,
                is_afk INTEGER DEFAULT 0,
                afk_reason TEXT,
                afk_since TEXT,
                custom_status TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS autoresponders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                trigger_word TEXT,
                response_text TEXT,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS game_stats (
                user_id INTEGER PRIMARY KEY,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                duels INTEGER DEFAULT 0
            )
        """)
        conn.commit()


def get_or_create_user(user_id: int, username: Optional[str] = None, full_name: Optional[str] = None) -> Dict[str, Any]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        now_name = full_name or "Пользователь"
        clean_user = (username or "").lstrip("@")

        if row:
            cur.execute("UPDATE users SET username = ?, full_name = ? WHERE user_id = ?", (clean_user, now_name, user_id))
            conn.commit()
            cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(cur.fetchone())

        cur.execute("""
            INSERT INTO users (user_id, username, full_name, stars, is_afk)
            VALUES (?, ?, ?, ?, 0)
        """, (user_id, clean_user, now_name, DEFAULT_STARS))
        cur.execute("INSERT OR IGNORE INTO game_stats (user_id) VALUES (?)", (user_id,))
        conn.commit()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return dict(cur.fetchone())


def set_afk(user_id: int, reason: str = "Отошёл") -> None:
    now = datetime.datetime.now().strftime("%H:%M:%S (%d.%m)")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_afk = 1, afk_reason = ?, afk_since = ? WHERE user_id = ?", (reason, now, user_id))
        conn.commit()


def clear_afk(user_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT is_afk, afk_reason, afk_since FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row and row["is_afk"]:
            cur.execute("UPDATE users SET is_afk = 0, afk_reason = NULL, afk_since = NULL WHERE user_id = ?", (user_id,))
            conn.commit()
            return dict(row)
        return None


def get_afk_info(user_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT is_afk, afk_reason, afk_since FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row and row["is_afk"]:
            return dict(row)
        return None


def update_stars(user_id: int, amount: int) -> int:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET stars = MAX(0, stars + ?) WHERE user_id = ?", (amount, user_id))
        conn.commit()
        cur.execute("SELECT stars FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return row["stars"] if row else 0


def set_custom_status(user_id: int, status: str) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET custom_status = ? WHERE user_id = ?", (status, user_id))
        conn.commit()


def add_autoresponder(user_id: int, trigger: str, response: str) -> None:
    now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO autoresponders (user_id, trigger_word, response_text, created_at) VALUES (?, ?, ?, ?)",
                    (user_id, trigger.lower().strip(), response.strip(), now))
        conn.commit()


def get_autoresponders(user_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM autoresponders WHERE user_id = ?", (user_id,))
        return [dict(r) for r in cur.fetchall()]


def delete_autoresponder(user_id: int, trigger: str) -> bool:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM autoresponders WHERE user_id = ? AND trigger_word = ?", (user_id, trigger.lower().strip()))
        conn.commit()
        return cur.rowcount > 0


def update_game_win(winner_id: int, loser_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE game_stats SET wins = wins + 1, duels = duels + 1 WHERE user_id = ?", (winner_id,))
        cur.execute("UPDATE game_stats SET losses = losses + 1, duels = duels + 1 WHERE user_id = ?", (loser_id,))
        conn.commit()
