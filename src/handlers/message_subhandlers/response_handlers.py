from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from datetime import datetime
from pytz import timezone
from ...services import database_service as db
from ...services.file_storage import FileStorage
from ... import config
from .utils import sanitize_text

logger = logging.getLogger(__name__)
storage = FileStorage(config.STORAGE_PATH)
ist = timezone("Asia/Kolkata")

async def handle_text_response(update: Update, context: ContextTypes.DEFAULT_TYPE, slot: dict, event_id: int):
    """Handle text message for a slot."""
    message = update.message
    group_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    username = message.from_user.username or ""
    last_name = message.from_user.last_name or ""
    text = sanitize_text(message.text)
    display_name = username or first_name or "You"

    slot_id = slot["slot_id"]
    slot_name = slot["slot_name"]

    keywords = db.get_slot_keywords(slot_id)
    text_lower = text.lower()
    keyword_match = any(keyword.lower() in text_lower for keyword in keywords)

    if keyword_match:
        points = slot["slot_points"]

        db.add_points(group_id, user_id, points, event_id)
        db.log_activity(group_id=group_id, user_id=user_id, activity_type="text", slot_name=slot_name,
                        username=username, first_name=first_name, last_name=last_name, message_content=text,
                        points_earned=points)

        await message.reply_text(f'✅ {display_name} scored {points} points!')
        logger.info(f"User {user_id} completed slot {slot_name} with text")

    else:
        keyboard = [
            [InlineKeyboardButton("✅ Yes", callback_data=f"confirm_yes_{slot_id}_{user_id}_{message.message_id}"),
             InlineKeyboardButton("❌ No", callback_data=f"confirm_no_{slot_id}_{user_id}_{message.message_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        confirmation_msg = await message.reply_text(slot["response_clarify"], reply_markup=reply_markup)

        if "pending_confirmations" not in context.bot_data:
            context.bot_data["pending_confirmations"] = {}

        context.bot_data["pending_confirmations"][confirmation_msg.message_id] = {
            "user_id": user_id, "username": username, "first_name": first_name, "last_name": last_name,
            "slot_id": slot_id, "slot_name": slot_name, "event_id": event_id, "group_id": group_id,
            "original_message_id": message.message_id, "text": text, "points": slot["slot_points"], "type": "text"
        }

        context.job_queue.run_once(
            auto_reject_confirmation,
            when=config.CONFIRMATION_TIMEOUT,
            data={"confirmation_msg_id": confirmation_msg.message_id},
        )

async def handle_photo_response(update: Update, context: ContextTypes.DEFAULT_TYPE, slot: dict, event_id: int):
    """Handle photo message for a slot."""
    message = update.message
    group_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    username = message.from_user.username or ""
    last_name = message.from_user.last_name or ""
    display_name = username or first_name or "You"

    slot_id = slot["slot_id"]
    slot_name = slot["slot_name"]

    # Get the largest photo
    photo = message.photo[-1]
    file_id = photo.file_id

    # Check if photo has a caption with keyword match
    caption = message.caption if message.caption else ""
    keywords = db.get_slot_keywords(slot_id)

    caption_lower = caption.lower()
    keyword_match = (
        any(keyword.lower() in caption_lower for keyword in keywords)
        if keywords and caption
        else False
    )

    if keyword_match or not keywords:
        # Direct match OR no keywords defined (all photos accepted) - award points
        try:
            # Download and save photo
            file = await context.bot.get_file(file_id)

            # Create formatted filename: {username}_{slotname}_{YYYY_MM_DD_HH_MM_SS_am/pm}.jpg
            timestamp = datetime.now(ist).strftime("%Y_%m_%d_%I_%M_%S_%p").lower()
            filename = f"{username}_{slot_name}_{timestamp}.jpg"

            # Save file with new structure
            local_path = await storage.save_photo(group_id, user_id, username, slot_name, file, filename)

            # Award points
            points = slot["slot_points"]
            db.add_points(group_id=group_id, user_id=user_id, points=points, event_id=event_id)
            db.log_activity(group_id=group_id, user_id=user_id, slot_name=slot_name, username=username,
                            first_name=first_name, last_name=last_name, activity_type="photo",
                            telegram_file_id=file_id, local_file_path=local_path, points_earned=points,
                            )

            if event_id:
                db.mark_slot_completed(group_id=group_id, event_id=event_id, slot_id=slot_id, user_id=user_id, status="completed", points=points)

            await message.reply_text(f'✅ {display_name} scored {points} points!')
            logger.info(f"User {user_id} completed slot {slot_name} with photo")

        except Exception as e:
            logger.error(f"Error handling photo: {e}", exc_info=True)
            await message.reply_text("Sorry, there was an error processing your photo. Please try again.")

    else:
        # Keywords exist but no match - ask for confirmation
        keyboard = [
            [InlineKeyboardButton("✅ Yes", callback_data=f"confirm_yes_{slot_id}_{user_id}_{message.message_id}"),
             InlineKeyboardButton("❌ No", callback_data=f"confirm_no_{slot_id}_{user_id}_{message.message_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        confirmation_msg = await message.reply_text(slot["response_clarify"], reply_markup=reply_markup)

        # Store confirmation data in context
        if "pending_confirmations" not in context.bot_data:
            context.bot_data["pending_confirmations"] = {}

        context.bot_data["pending_confirmations"][confirmation_msg.message_id] = {
            "user_id": user_id, "first_name": first_name, "last_name": last_name, "slot_id": slot_id,
            "slot_name": slot_name, "event_id": event_id, "group_id": group_id, "original_message_id": message.message_id,
            "photo_file_id": file_id, "username": username, "caption": caption, "points": slot["slot_points"],
            "type": "photo",
        }

        # Auto-select "No" after timeout
        context.job_queue.run_once(
            auto_reject_confirmation,
            when=config.CONFIRMATION_TIMEOUT,
            data={"confirmation_msg_id": confirmation_msg.message_id},
        )


async def handle_other_media_response(
    update: Update, context: ContextTypes.DEFAULT_TYPE, slot: dict, event_id: int
):
    """Handle other media types (video, sticker, document, etc.) for a photo slot."""
    message = update.message
    group_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    username = message.from_user.username or ""
    last_name = message.from_user.last_name or ""

    slot_id = slot["slot_id"]
    slot_name = slot["slot_name"]

    # Determine media type and file extension
    media_type = None
    file_id = None
    file_ext = None

    if message.video:
        media_type = "video"
        file_id = message.video.file_id
        file_ext = "mp4"
    elif message.document:
        media_type = "document"
        file_id = message.document.file_id
        # Get original filename extension if available
        if message.document.file_name:
            file_ext = (message.document.file_name.split(".")[-1] if "." in message.document.file_name else "file")
        else:
            file_ext = "file"
    elif message.sticker:
        media_type = "sticker"
        file_id = message.sticker.file_id
        file_ext = "webp"
    elif message.animation:
        media_type = "animation"
        file_id = message.animation.file_id
        file_ext = "gif"
    elif message.voice:
        media_type = "voice"
        file_id = message.voice.file_id
        file_ext = "ogg"
    elif message.video_note:
        media_type = "video_note"
        file_id = message.video_note.file_id
        file_ext = "mp4"

    # Determine points based on media type
    if media_type in ["video", "document", "voice", "video_note", "sticker", "animation"]:
        points = slot["slot_points"]
    else:
        points = slot["slot_points"]

    keyboard = [
        [InlineKeyboardButton("✅ Yes", callback_data=f"confirm_yes_{slot_id}_{user_id}_{message.message_id}"),
         InlineKeyboardButton("❌ No", callback_data=f"confirm_no_{slot_id}_{user_id}_{message.message_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # points_msg = f" ({points} points)" if points > 0 else " (no points)"
    confirmation_msg = await message.reply_text(f"{first_name}, Is this your {slot_name} ?", reply_markup=reply_markup)

    # Store confirmation data in context
    if "pending_confirmations" not in context.bot_data:
        context.bot_data["pending_confirmations"] = {}

    context.bot_data["pending_confirmations"][confirmation_msg.message_id] = {
        "user_id": user_id, "first_name": first_name, "last_name": last_name, "slot_id": slot_id,
        "slot_name": slot_name, "event_id": event_id, "group_id": group_id, "original_message_id": message.message_id,
        "file_id": file_id, "username": username, "caption": message.caption if message.caption else "",
        "points": points, "type": "media", "media_type": media_type, "file_ext": file_ext,
    }

    # Auto-select "No" after timeout
    context.job_queue.run_once(
        auto_reject_confirmation,
        when=config.CONFIRMATION_TIMEOUT,
        data={"confirmation_msg_id": confirmation_msg.message_id},
    )


async def auto_reject_confirmation(context: ContextTypes.DEFAULT_TYPE):
    """Auto-rejects confirmation for a user after timeout."""
    job = context.job
    confirmation_msg_id = job.data["confirmation_msg_id"]

    if "pending_confirmations" in context.bot_data:
        if confirmation_msg_id in context.bot_data["pending_confirmations"]:
            data = context.bot_data["pending_confirmations"][confirmation_msg_id]

            if data:
                try:
                    # Deletes the user's original message that was rejected
                    original_message_id = data.get("original_message_id")
                    if original_message_id:
                        await context.bot.delete_message(chat_id=data["group_id"], message_id=original_message_id)
                        logger.info(f"Deleted timed-out message {original_message_id}")

                    await context.bot.edit_message_text(
                        chat_id=data["group_id"],
                        message_id=confirmation_msg_id,
                        text="⏱️ Timeout didn't get a confirmation!",
                    )

                    # Deletes the "Timeout" message itself after 3 seconds
                    context.job_queue.run_once(
                        lambda ctx: context.bot.delete_message(data["group_id"], confirmation_msg_id), when=5)

                    # Logs that the activity was invalid
                    db.log_activity(group_id=data["group_id"], user_id=data["user_id"], username=data["username"],
                                    first_name=data["first_name"], last_name=data["last_name"],
                                    slot_name=data["slot_name"], activity_type=data.get("type", "text"),
                                    message_content=data.get("text", ""), points_earned=0, is_valid=False)

                except Exception as e:
                    logger.error(f"Error in auto-reject: {e}", exc_info=True)