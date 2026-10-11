"""
SQLite Database Layer for Telegram Username Bot
Supports Users, Search Quotas, Premium Subscriptions, History, Banning, and Admin Analytics.
"""
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from config import DATABASE_PATH, DEFAULT_FREE_QUERIES, DEFAULT_PROMOCODES


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables and handle column migrations"""
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
                registered_at TEXT,
                is_banned INTEGER DEFAULT 0
            )
        """)

        # Check and add is_banned column if migrated from older version
        cursor.execute("PRAGMA table_info(users)")
        columns = [col["name"] for col in cursor.fetchall()]
        if "is_banned" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")

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

        cursor.execute("PRAGMA table_info(promocodes)")
        promo_cols = [col["name"] for col in cursor.fetchall()]
        if "created_at" not in promo_cols:
            cursor.execute("ALTER TABLE promocodes ADD COLUMN created_at TEXT")

        # Seed initial promo codes
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        for code in DEFAULT_PROMOCODES:
            cursor.execute(
                "INSERT OR IGNORE INTO promocodes (code, is_used, created_at) VALUES (?, 0, ?)",
                (code.upper(), now)
            )

        conn.commit()


def get_or_create_user(user_id: int, username: Optional[str], full_name: str) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        clean_username = (username or "").lstrip("@").lower()

        if row:
            cursor.execute(
                "UPDATE users SET username = ?, full_name = ? WHERE user_id = ?",
                (clean_username, full_name, user_id)
            )
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(cursor.fetchone())

        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        cursor.execute("""
            INSERT INTO users (user_id, username, full_name, is_premium, queries_left, total_searches, registered_at, is_banned)
            VALUES (?, ?, ?, 0, ?, 0, ?, 0)
        """, (user_id, clean_username, full_name, DEFAULT_FREE_QUERIES, now))
        conn.commit()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return dict(cursor.fetchone())


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def is_user_banned(user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return bool(row["is_banned"]) if row else False


def set_user_ban(user_id: int, banned: bool) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (1 if banned else 0, user_id))
        conn.commit()
        return cursor.rowcount > 0


def set_user_premium(user_id: int, premium: bool) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_premium = ? WHERE user_id = ?", (1 if premium else 0, user_id))
        conn.commit()
        return cursor.rowcount > 0


def add_user_queries(user_id: int, count: int) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET queries_left = queries_left + ? WHERE user_id = ?", (count, user_id))
        conn.commit()
        cursor.execute("SELECT queries_left FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row["queries_left"] if row else 0


def can_search(user_id: int) -> bool:
    user = get_user(user_id)
    if not user:
        return False
    if user["is_banned"]:
        return False
    if user["is_premium"]:
        return True
    return user["queries_left"] > 0


def consume_search(user_id: int) -> bool:
    """Consume one search query if not premium. Returns True if consumed successfully."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_banned, is_premium, queries_left, total_searches FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row or row["is_banned"]:
            return False

        is_prem, queries_left = row["is_premium"], row["queries_left"]

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
    return set_user_premium(user_id, True)


def redeem_promocode(user_id: int, code: str) -> Tuple[bool, str]:
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
        return True, "🎉 Премиум успешно активирован! Теперь у вас безлимитный доступ к поиску."


def create_promocode(code: str) -> bool:
    clean_code = code.strip().upper()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO promocodes (code, is_used, created_at) VALUES (?, 0, ?)", (clean_code, now))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def get_all_promocodes() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM promocodes ORDER BY is_used ASC, rowid DESC LIMIT 30")
        return [dict(r) for r in cursor.fetchall()]


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


# --------------------------------------------------------------------------
# Admin Specific Database Queries
# --------------------------------------------------------------------------

def get_admin_stats() -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
        premium_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        banned_users = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(total_searches), 0) FROM users")
        total_searches = cursor.fetchone()[0]

        today_prefix = datetime.now().strftime("%d.%m.%Y")
        cursor.execute("SELECT COUNT(*) FROM found_history WHERE created_at LIKE ?", (f"{today_prefix}%",))
        searches_today = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM promocodes WHERE is_used = 0")
        active_promos = cursor.fetchone()[0]

        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "banned_users": banned_users,
            "total_searches": total_searches,
            "searches_today": searches_today,
            "active_promos": active_promos
        }


def find_user_by_query(query: str) -> Optional[Dict[str, Any]]:
    """Search user by ID or exact @username"""
    clean = query.strip().lstrip("@").lower()
    with get_connection() as conn:
        cursor = conn.cursor()
        if clean.isdigit():
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (int(clean),))
            row = cursor.fetchone()
            if row:
                return dict(row)

        cursor.execute("SELECT * FROM users WHERE LOWER(username) = ?", (clean,))
        row = cursor.fetchone()
        if row:
            return dict(row)

        cursor.execute("SELECT * FROM users WHERE LOWER(full_name) LIKE ? LIMIT 1", (f"%{clean}%",))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_users_page(page: int = 1, page_size: int = 6) -> Tuple[List[Dict[str, Any]], int, int]:
    offset = (page - 1) * page_size
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_count = cursor.fetchone()[0]
        total_pages = max(1, (total_count + page_size - 1) // page_size)

        cursor.execute("""
            SELECT * FROM users 
            ORDER BY user_id DESC 
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        users = [dict(r) for r in cursor.fetchall()]
        return users, total_pages, total_count


def get_all_user_ids() -> List[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE is_banned = 0")
        return [row[0] for row in cursor.fetchall()]
