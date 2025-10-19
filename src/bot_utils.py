import asyncio
import logging
from telegram import Update, CallbackQuery, Message
from telegram.ext import ContextTypes
from telegram.error import RetryAfter, TimedOut

logger = logging.getLogger(__name__)

# safely send messages
async def safe_send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, max_retries: int = 2, **kwargs) -> Message | None:
    """
    Safely sends a message, handling common Telegram API errors like rate limits and timeouts.
    """
    for attempt in range(max_retries):
        try:
            message = message = await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)
            return message
        except RetryAfter as e:
            logger.warning("Rate limit exceeded for chat %s. Waiting for %s seconds. Attempt %s/%s.", chat_id, e.retry_after, attempt + 1, max_retries,exc_info=True)
            message = await asyncio.sleep(e.retry_after)
        except TimedOut:
            wait_time = 5 * (attempt + 1)
            logger.warning("Telegram API timed out for chat %s. Retrying in %s seconds. Attempt %s/%s.", chat_id, wait_time, attempt + 1, max_retries,exc_info=True)
            message = await asyncio.sleep(wait_time)
        except Exception as e:
            logger.error("An unexpected error occurred while sending message to chat %s: %s", chat_id, e, exc_info=True)
            return None

    logger.error("Failed to send message to chat %s after %s retries.", chat_id, max_retries, exc_info=True)
    return None

# safely replies ot messages
async def safe_reply_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, max_retries: int = 2, **kwargs) -> Message | None:
    for attempt in range(max_retries):
        try:
            message = await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_to_message_id=update.message.message_id, **kwargs)
            return message
        except RetryAfter as e:
            logger.warning("Rate limit on reply. Waiting %s s.", e.retry_after,exc_info=True)
            message = await asyncio.sleep(e.retry_after)
        except TimedOut:
            logger.warning("Timeout on reply. Retrying...",exc_info=True)
            message = await asyncio.sleep(5 * (attempt + 1))
        except Exception as e:
            logger.error("Failed to send reply: %s", e, exc_info=True)
            return None

    logger.error("Failed to send reply after %s retries.", max_retries,exc_info=True)
    return None

# safely edits messages
async def safe_edit_message_text(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, text: str, max_retries: int = 2, **kwargs) -> Message | None:
    for attempt in range(max_retries):
        try:
            message = await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, **kwargs)
            return message
        except RetryAfter as e:
            logger.warning("Rate limit on edit. Waiting %s s.", e.retry_after,exc_info=True)
            message = await asyncio.sleep(e.retry_after)
        except TimedOut:
            logger.warning("Timeout on edit. Retrying...",exc_info=True)
            message = await asyncio.sleep(5 * (attempt + 1))
        except Exception as e:
            logger.error("Failed to edit message: %s", e, exc_info=True)
            return None

    logger.error("Failed to edit message after %s retries.", max_retries,exc_info=True)
    return None


async def safe_callback_reply_text(query: "CallbackQuery", context: ContextTypes.DEFAULT_TYPE, text: str, max_retries: int = 2, **kwargs) -> Message | None:
    """
    Safely replies to the message that a callback query originated from.
    """
    if not query.message:
        return None # Cannot reply if the original message is gone

    for attempt in range(max_retries):
        try:
            message = await context.bot.send_message(chat_id=query.message.chat_id, text=text, reply_to_message_id=query.message.message_id, **kwargs)
            return message
        except RetryAfter as e:
            logger.warning("Rate limit on callback reply. Waiting %s s.", e.retry_after)
            message = await asyncio.sleep(e.retry_after)
        except TimedOut:
            logger.warning("Timeout on callback reply. Retrying...")
            message = await asyncio.sleep(5 * (attempt + 1))
        except Exception as e:
            logger.error("Failed to send callback reply: %s", e, exc_info=True)
            return None

    logger.error("Failed to send callback reply after %s retries.", max_retries)
    return None