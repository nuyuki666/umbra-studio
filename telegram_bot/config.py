"""
Configuration settings for Mod_SaveBot clone
"""
import os

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

BOT_TOKEN = os.getenv("BOT_TOKEN", "8857554794:AAE8tM8IvdBu4btAGBpC1NVYP3hL-BsKGzg")
ADMIN_IDS = [8810231186]
COMMAND_PREFIXES = (".", "/")
DB_PATH = os.path.join(os.path.dirname(__file__), "mod_bot.sqlite3")
DEFAULT_STARS = 100
