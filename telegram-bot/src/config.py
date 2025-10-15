import os
from dotenv import load_dotenv

load_dotenv(override=False)

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")

# MySQL Database
DB_HOST = os.getenv("DB_HOST", "localhost")
try:
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
except ValueError:
    DB_PORT = 3306
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_NAME = os.getenv("DB_NAME", "telegram_bot_manager")

# Bot Settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Inactivity Settings
try:
    INACTIVITY_DAYS = int(os.getenv("INACTIVITY_DAYS", "3"))
except ValueError:
    INACTIVITY_DAYS = 3

# Confirmation Timeout
try:
    CONFIRMATION_TIMEOUT = int(os.getenv("CONFIRMATION_TIMEOUT", "15"))
except ValueError:
    CONFIRMATION_TIMEOUT = 15

# Storage Path
STORAGE_PATH = os.getenv("STORAGE_PATH", "storage")
# os.makedirs(STORAGE_PATH, exist_ok=True)  # ensure path exists

# New Member Restriction Settings (in minutes)
try:
    NEW_MEMBER_RESTRICTION_MINUTES = int(
        os.getenv("NEW_MEMBER_RESTRICTION_MINUTES", "10")
    )
except ValueError:
    NEW_MEMBER_RESTRICTION_MINUTES = 10
