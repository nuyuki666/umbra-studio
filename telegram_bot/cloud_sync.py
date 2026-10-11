"""
Asynchronous Cloud Neon PostgreSQL Syncer for Telegram Bot
Keeps all users, searches, and history backed up in cloud database in real time.
"""
import aiohttp
import json
import logging

logger = logging.getLogger("neon_sync")

NEON_SQL_URL = "https://ep-cold-breeze-avl01r33-pooler.c-11.us-east-1.aws.neon.tech/sql"
NEON_CONN_STR = "postgresql://neondb_owner:npg_DJ9xBOlZcmd8@ep-cold-breeze-avl01r33-pooler.c-11.us-east-1.aws.neon.tech/neondb?sslmode=require"

BACKUP_SQL_URL = "https://ep-rapid-tooth-b8gvxrrp-pooler.c-14.us-east-1.aws.neon.tech/sql"
BACKUP_CONN_STR = "postgresql://neondb_owner:npg_Lp5TF9zwEJMc@ep-rapid-tooth-b8gvxrrp-pooler.c-14.us-east-1.aws.neon.tech/neondb?sslmode=require"


async def execute_neon_query(sql: str, params: list = None) -> bool:
    payload = json.dumps({"query": sql, "params": params or []})
    timeout = aiohttp.ClientTimeout(total=4.0)
    
    # Try primary
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                NEON_SQL_URL,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Neon-Connection-String": NEON_CONN_STR
                }
            ) as resp:
                if resp.status == 200:
                    return True
    except Exception as e:
        logger.debug(f"Primary Neon sync failed: {e}")

    # Fallback to backup
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                BACKUP_SQL_URL,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Neon-Connection-String": BACKUP_CONN_STR
                }
            ) as resp:
                return resp.status == 200
    except Exception:
        return False


async def sync_user_to_cloud(user_id: int, username: str, full_name: str, is_premium: bool, queries_left: int, total_searches: int):
    sql = f"""
    INSERT INTO tg_bot_users (user_id, username, full_name, is_premium, queries_left, total_searches, last_active)
    VALUES ({user_id}, '{(username or "").replace("'", "''")}', '{(full_name or "").replace("'", "''")}', {str(is_premium).lower()}, {queries_left}, {total_searches}, CURRENT_TIMESTAMP)
    ON CONFLICT (user_id) DO UPDATE SET
        username = EXCLUDED.username,
        full_name = EXCLUDED.full_name,
        is_premium = EXCLUDED.is_premium,
        queries_left = EXCLUDED.queries_left,
        total_searches = EXCLUDED.total_searches,
        last_active = CURRENT_TIMESTAMP;
    """
    await execute_neon_query(sql)


async def sync_search_to_cloud(user_id: int, username: str, length: int, ton_price: int):
    sql = f"""
    INSERT INTO tg_bot_history (user_id, username_checked, length, ton_price)
    VALUES ({user_id}, '{username.replace("'", "''")}', {length}, {ton_price});
    """
    await execute_neon_query(sql)
