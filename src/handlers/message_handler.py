from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import MessageHandler, filters, ContextTypes
import logging
from datetime import datetime, timedelta
import re
from pytz import timezone, utc
from services import database_service as db
from services.file_storage import FileStorage
import config
from handlers.start_handler import points, schedule
from db import execute_query
from bot_utils import safe_send_message

logger = logging.getLogger(__name__)
storage = FileStorage(config.STORAGE_PATH)
ist=timezone("Asia/Kolkata")

def sanitize_text(text):
    """Remove HTML tags and URLs from text."""
    if not text: return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove URLs
    text = re.sub(r"http[s]?://\S+", "", text)
    return text.strip()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages in groups."""
    message = update.message

    # Only handle group messages
    if message.chat.type not in ["group", "supergroup"]:
        return

    group_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    if message.text and message.text in ["My Score 💯", "Time Sheet 📅"]:
        if message.text == "My Score 💯": await points(update, context)
        elif message.text == "Time Sheet 📅": await schedule(update, context)
        return

    # Check if group is configured
    group_config = db.get_group_config(group_id)
    if not group_config:
        logger.warning(f"Group {group_id} not configured yet")
        return

    # Ensure member exists in database
    member, is_new = db.add_member(group_id, user_id, username, first_name, restrict_new=False)

    # Update member activity
    db.update_member_activity(group_id, user_id)

    # Check if user is admin first - admins are NEVER restricted and EXEMPT from all penalties
    member = db.get_member(group_id, user_id)
    
    if member and member.get("is_restricted") and member.get("restriction_until"):
        restriction_until_utc = member.get("restriction_until")  # Fetch raw datetime from DB (likely naive UTC)

        # Ensure it's a datetime object (if stored as string somehow, convert)
        if isinstance(restriction_until_utc, str):
            try:
                # Assuming the string format from DB is standard UTC
                restriction_until_utc = datetime.strptime(restriction_until_utc, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logger.error(f"Could not parse restriction_until string: {restriction_until_utc}")
                # Handle error appropriately, maybe skip restriction check
                restriction_until_utc = None

        if restriction_until_utc:
            # 1. Make the naive UTC datetime timezone-aware
            restriction_until_utc_aware = utc.localize(restriction_until_utc)

            # 2. Convert aware UTC time to aware IST time
            restriction_until_ist_aware = restriction_until_utc_aware.astimezone(ist)

            # 3. Get current time in IST (already aware)
            now_ist_aware = datetime.now(ist)

            # 4. Compare aware datetimes
            if now_ist_aware > restriction_until_ist_aware:
                start_date = now_ist_aware.date()  # Use the current IST date
                end_date = start_date + timedelta(days=7)
                # Restriction has expired, update the database
                query = "UPDATE group_members SET is_restricted = 0, restriction_until = NULL, cycle_start_date = %s, cycle_end_date = %s WHERE group_id = %s AND user_id = %s"
                execute_query(query, (start_date, end_date, group_id, user_id))
                # Refresh member data
                member = db.get_member(group_id, user_id)
                logger.info(f"Lifted expired restriction for user {user_id} in group {group_id}.")
            else:
                logger.info(f"User {user_id} was manually unrestricted by an admin. Syncing database.")
                start_date = now_ist_aware.date()
                end_date = start_date + timedelta(days=7)
                query = "UPDATE group_members SET is_restricted = 0, restriction_until = NULL, cycle_start_date = %s, cycle_end_date = %s WHERE group_id = %s AND user_id = %s"
                execute_query(query, (start_date, end_date, group_id, user_id))
                # Refresh member data so the rest of the function works
                member = db.get_member(group_id, user_id)

    # Also check if user is currently a Telegram admin/creator
    is_telegram_admin = member and member.get("is_admin", 0) == 1

    # Send welcome if new member
    if is_new:
        welcome_message = group_config.get("welcome_message", "Welcome!")
        welcome_text = f"Hi {first_name}, {welcome_message}"

        restriction_until_str = member.get("restriction_until")
        if (member.get("is_restricted") and restriction_until_str and not is_telegram_admin):
            if isinstance(restriction_until_str, str):
                restriction_until_dt = datetime.strptime(restriction_until_str, "%Y-%m-%d %H:%M:%S")
            else:
                restriction_until_dt = restriction_until_str

        if is_telegram_admin:
            welcome_text += "\n\nAs an admin, you have full access immediately! 💼"

        await safe_send_message(context=context, chat_id=group_id, text=welcome_text)

    # Check database admin
    is_db_admin = group_config and group_config.get("admin_user_id") == user_id

    # User is admin if they're either Telegram admin OR database admin
    is_admin = is_telegram_admin or is_db_admin

    # If user is admin but was restricted, unrestrict them immediately
    if is_admin and member and member.get("is_restricted", 0) == 1:
        try:
            chat_member = await context.bot.get_chat_member(group_id, user_id)
        
            # Only try to change admin permissions if the user is not the creator
            if chat_member.status != 'creator':
                await context.bot.restrict_chat_member(
                    chat_id=group_id,
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=True, can_send_other_messages=True)
                )

            # Update database
            query = "UPDATE group_members SET is_restricted = 0, restriction_until = NULL WHERE group_id = %s AND user_id = %s"
            execute_query(query, (group_id, user_id))

            logger.info(f"Admin {user_id} was restricted but has now been unrestricted in group {group_id}")
        except Exception as e:
            logger.error(f"Error unrestricting admin: {e}",exc_info=True)

    # Check for banned words FIRST - ALWAYS ban on 2 warnings regardless of points (EXCEPT ADMINS)
    if message.text and not is_admin:
        custom_banned = db.get_banned_words(group_id)

        if not custom_banned: logger.warning(f"No banned words found for group {group_id}. Check database!")

        message_text_lower = message.text.lower()

        # Check if ANY banned word appears in the message with word boundaries
        matched_word = None
        for banned_word in custom_banned:
            # Use word boundaries for single words, substring for phrases
            if " " in banned_word:
                # Multi-word phrases: substring match
                if banned_word.lower() in message_text_lower:
                    matched_word = banned_word
                    logger.warning(f"BANNED PHRASE MATCH: '{banned_word}' found in '{message.text[:50]}'")
                    break
            else:
                pattern = r"\b" + re.escape(banned_word.lower()) + r"\b"
                if re.search(pattern, message_text_lower):
                    matched_word = banned_word
                    logger.warning(f"BANNED WORD MATCH: '{banned_word}' found in '{message.text[:50]}'")
                    break

        if matched_word:
            try:
                await message.delete()
                db.add_banned_words_warning(group_id, user_id)

                # Deduct 10 knockout points for banned word
                db.deduct_knockout_points(group_id, user_id, 10)

                member = db.get_member(group_id, user_id)
                warnings = member["banned_word_count"] if member else 1
                total_points = member["total_points"] if member else 0

                warning_msg = await safe_send_message(
                    context=context, 
                    chat_id=group_id,
                    text=f"⚠️ {first_name}, please avoid using inappropriate language!\n"
                    f"Warning {warnings}/2. Using banned word: '{matched_word}'\n",
                )

                context.job_queue.run_once(lambda _: warning_msg.delete(), when=5)

                if warnings >= 2:
                    try:
                        until_date = datetime.now(ist) + timedelta(minutes=1)

                        await context.bot.ban_chat_member(group_id, user_id, until_date=until_date)

                        db.remove_member(group_id, user_id, "kicked")
                        logger.warning(f"User {user_id} record has been DELETED from the database.")
                        
                        await context.bot.unban_chat_member(group_id, user_id)

                        if total_points >= 100:
                            kick_msg = (
                                f"👋 {first_name} earned {total_points} points but has been REMOVED from the group.\n"
                                f"Reason: 2 warnings for using banned words.\n"
                            )
                        else:
                            kick_msg = (
                                f"🚫 {first_name} has been REMOVED from the group.\n"
                                f"Reason: 2 warnings for using banned words.\n"
                            )

                        await safe_send_message(context=context, chat_id=group_id, text=kick_msg)
                        logger.warning(f"User {user_id} ({first_name}) kicked for 2 banned word violations")

                    except Exception as ban_error:
                        logger.error(f"Failed to apply 24-hour ban for user {user_id}: {ban_error}")
                        await safe_send_message(
                            context=context, 
                            chat_id=group_id,
                            text=f"⚠️ Could not ban {first_name}. Please check my admin permissions.",
                        )

                logger.warning(f"Banned word detected from user {user_id}: {matched_word}")
                return

            except Exception as e:
                logger.error(f"Error handling banned word: {e}",exc_info=True)

    # Get active slot
    active_slot = db.get_active_slot(group_id)

    if not active_slot:
        # No active slot - delete message, warn, and deduct knockout points
        try:
            await message.delete()
            db.add_general_warning(group_id, user_id)

            # Deduct 5 knockout points for posting outside slot
            db.deduct_knockout_points(group_id, user_id, 5)

            warning_msg = await safe_send_message(
                context=context, 
                chat_id=group_id,
                text=f"⏰ {first_name}, no active slot right now!\n"
                f"Please only post during designated time slots.\n",
            )

            # Delete warning after 10 seconds
            context.job_queue.run_once(lambda _: warning_msg.delete(), when=10)
            logger.info(f"Message outside slot from user {user_id} - knockout points deducted")
            return

        except Exception as e:
            logger.error(f"Error deleting message: {e}",exc_info=True)
            return

    # Handle message based on slot type and content
    slot_id = active_slot["slot_id"]
    slot_name = active_slot["slot_name"]
    slot_type = active_slot["slot_type"]

    # Get active event
    event = db.get_active_event(group_id)
    event_id = event["event_id"] if event else None

    # Check if already completed today
    if event_id and db.check_slot_completed_today(event_id, slot_id, user_id):
        try:
            # If it's a duplicate, delete the message and inform the user.
            await message.delete()
            info_msg = await safe_send_message(
                context=context,
                chat_id=group_id,
                text=f"✅ {first_name}, you've already completed this slot today!",
            )
            
            async def delete_info_msg(context):
                if info_msg:
                    await info_msg.delete()
            context.job_queue.run_once(delete_info_msg,when=5)
            return
        except Exception as e:
            logger.error(f"Error handling duplicate submission: {e}", exc_info=True)
            return
        
    if slot_type == "button":
        try:
            await message.delete()
            warning_msg = await safe_send_message(
                context=context,
                chat_id=group_id,
                text=f"⏰ {first_name}, please use the buttons for the {slot_name} slot!\n"
                     f"Messages are not accepted right now.",
            )
            # Delete warning after 10 seconds
            context.job_queue.run_once(lambda _: warning_msg.delete(), when=10)
            logger.info(f"Deleted invalid message from user {user_id} during button slot {slot_name}")
            return  # Stop all further processing
        except Exception as e:
            logger.error(f"Error deleting message during button slot: {e}", exc_info=True)
            return
        
    # Accept ANY media type for regular slots except button typed
    if message.photo:
        await handle_photo_response(update, context, active_slot, event_id)

    elif message.text:
        await handle_text_response(update, context, active_slot, event_id)

    elif (message.video or message.document or message.sticker or message.animation or message.voice or message.video_note):
        # Other media types - ask for confirmation
        await handle_other_media_response(update, context, active_slot, event_id)

    else:
        # Unknown content type
        logger.warning(f"Unknown message type from user {user_id} in group {group_id}")


async def handle_text_response(update: Update, context: ContextTypes.DEFAULT_TYPE, slot: dict, event_id: int):
    """Handle text message for a slot."""
    message = update.message
    group_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    username = message.from_user.username or ""
    last_name = message.from_user.last_name or ""
    text = sanitize_text(message.text)
    display_name=username or first_name or "You"

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
    last_name=message.from_user.last_name or ""
    display_name= username or first_name or "You"

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
            logger.error(f"Error handling photo: {e}",exc_info=True)
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
    last_name=message.from_user.last_name or ""

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
    if media_type in ["video", "document", "voice", "video_note", "sticker", "animation"]: points = slot["slot_points"]
    else: points = slot["slot_points"]

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
                        lambda ctx: context.bot.delete_message(data["group_id"], confirmation_msg_id),when=5)

                    # Logs that the activity was invalid
                    db.log_activity(group_id=data["group_id"], user_id=data["user_id"], username=data["username"],
                                    first_name=data["first_name"], last_name=data["last_name"], 
                                    slot_name=data["slot_name"], activity_type=data.get("type", "text"),
                                    message_content=data.get("text", ""), points_earned=0, is_valid=False)

                except Exception as e:
                    logger.error(f"Error in auto-reject: {e}",exc_info=True)


# Create message handlers
text_message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
photo_message_handler = MessageHandler(filters.PHOTO, handle_message)
video_message_handler = MessageHandler(filters.VIDEO, handle_message)
document_message_handler = MessageHandler(filters.Document.ALL, handle_message)
sticker_message_handler = MessageHandler(filters.Sticker.ALL, handle_message)
animation_message_handler = MessageHandler(filters.ANIMATION, handle_message)
voice_message_handler = MessageHandler(filters.VOICE, handle_message)
video_note_message_handler = MessageHandler(filters.VIDEO_NOTE, handle_message)