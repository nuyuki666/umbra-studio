"""
Configuration and constants for Telegram Username Finder Bot
"""
import os

# Telegram Bot Token: Reads from environment variable or uses placeholder
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

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

# Admin IDs (can be configured by user)
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
