"""
Configuration and constants for Telegram Username Finder Bot
"""
import os

# Telegram Bot Token: Verified active token for @UsernameSolisSearch_bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "8857554794:AAE8tM8IvdBu4btAGBpC1NVYP3hL-BsKGzg")

# Default settings
DEFAULT_FREE_QUERIES = 2
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite3")

# TON and Currency exchange rates for valuation estimation
TON_TO_USD = 5.8
USD_TO_RUB = 95.0

# Initial Promo Codes for Premium access
DEFAULT_PROMOCODES = [
    "PREMIUM2026",
    "VIPUSER",
    "FREEUNLIMITED",
    "TELEGRAM777"
]

# Admin IDs: Primary owner ID 8810231186
PRIMARY_ADMIN_ID = 8810231186
env_admins = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
ADMIN_IDS = list(set([PRIMARY_ADMIN_ID] + env_admins))
