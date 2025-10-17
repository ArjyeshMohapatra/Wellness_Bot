import logging
import sys
from telegram import Update
from telegram.ext import Application
import config
from handlers import setup_handlers
from db import init_db_pool

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
# Force all loggers to DEBUG
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("services.database_service").setLevel(logging.DEBUG)
logging.getLogger("handlers.join_handler").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


def main():
    """Start the bot."""
    try:
        # Validate configuration
        if not config.BOT_TOKEN:
            logger.error("BOT_TOKEN not found in .env file!")
            sys.exit(1)

        logger.info("Initializing Telegram Wellness Bot...")

        # Initialize database connection pool
        init_db_pool()
        logger.info("Database connection pool initialized")
        
        # Create the Application with post_init
        application = Application.builder().token(config.BOT_TOKEN).build()

        # Setup handlers
        setup_handlers(application)
        logger.info("All handlers registered")

        logger.info("Bot is starting... Press Ctrl+C to stop")

        # Run the bot until the user presses Ctrl-C
        application.run_polling(
            allowed_updates=["message", "chat_member", "callback_query"]
        )

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception:
        logger.error("Fatal error", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
