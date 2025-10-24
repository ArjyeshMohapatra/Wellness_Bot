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
    CONFIRMATION_TIMEOUT = int(os.getenv("CONFIRMATION_TIMEOUT", "60"))
except ValueError:
    CONFIRMATION_TIMEOUT = 60

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

""" # Authentication Settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")

# Email Settings for Password Reset
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
try:
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
except ValueError:
    SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USERNAME) """
