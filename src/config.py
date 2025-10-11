import os
from dotenv import load_dotenv

# Load .env file if it exists (for local development)
# Railway provides env vars directly, so this is optional
load_dotenv(override=False)

# Telegram Bot
BOT_TOKEN = os.getenv('BOT_TOKEN')

# MySQL Database
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT') or '3306')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '1234')
DB_NAME = os.getenv('DB_NAME', 'telegram_bot_manager')

# Debug logging for Railway
print(f"[CONFIG DEBUG] DB_HOST={DB_HOST}, DB_PORT={DB_PORT}, DB_USER={DB_USER}, DB_NAME={DB_NAME}")

# Bot Settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Inactivity Settings
INACTIVITY_DAYS = int(os.getenv('INACTIVITY_DAYS', '3'))

# Confirmation Timeout
CONFIRMATION_TIMEOUT = int(os.getenv('CONFIRMATION_TIMEOUT', '15'))

# Storage Path
STORAGE_PATH = os.getenv('STORAGE_PATH', 'storage')