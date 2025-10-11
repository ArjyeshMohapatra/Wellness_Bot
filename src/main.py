import logging
import sys
from telegram import Update
from telegram.ext import Application
from config import Config
from handlers import setup_handlers
from db import init_db_pool

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    try:
        config = Config()
        
        # Validate configuration
        if not config.BOT_TOKEN:
            logger.error("BOT_TOKEN not found in .env file!")
            sys.exit(1)
        
        logger.info("Initializing Telegram Wellness Bot...")
        
        # Initialize database connection pool
        init_db_pool()
        logger.info("Database connection pool initialized")
        
        # Create the Application
        application = Application.builder().token(config.BOT_TOKEN).build()
        
        # Initialize bot_data for storing pending confirmations
        application.bot_data['pending_confirmations'] = {}
        
        # Setup handlers
        setup_handlers(application)
        logger.info("All handlers registered")
        
        logger.info("Bot is starting... Press Ctrl+C to stop")
        
        # Run the bot until the user presses Ctrl-C
        application.run_polling(allowed_updates=[Update.MESSAGE, Update.CHAT_MEMBER, Update.CALLBACK_QUERY])
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()