from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, ReplyKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes
import logging
from datetime import datetime, timedelta
import re
from pytz import timezone, utc
from ..services import database_service as db
from ..services.file_storage import FileStorage
from .. import config
from .start_handler import points, schedule
from ..db import execute_query
from ..bot_utils import safe_send_message
from .message_subhandlers.utils import sanitize_text, extract_license_key
from .message_subhandlers.private_message_handler import handle_private_message, complete_kyc_process, handle_license_key
from .message_subhandlers.response_handlers import handle_text_response, handle_photo_response, handle_other_media_response, auto_reject_confirmation

logger = logging.getLogger(__name__)
storage = FileStorage(config.STORAGE_PATH)
ist=timezone("Asia/Kolkata")

# Utility functions are now imported from message_subhandlers.utils
# Private message handling functions are now imported from message_subhandlers.private_message_handler
# Response handling functions are now imported from message_subhandlers.response_handlers

# Private message handling functions moved to message_subhandlers.private_message_handler

# Main message handler function


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages in groups and private chats."""
    message = update.message

    # Handle private messages for user validation/KYC process
    if message.chat.type == "private":
        await handle_private_message(update, context)
        return

    # Check if bot was added to a group
    if message.new_chat_members:
        for member in message.new_chat_members:
            if member.id == context.bot.id:
                # Bot was added to this group
                logger.info(f"Bot added to group {message.chat.id} via message handler")
                from .join_handler import handle_bot_added_to_group
                await handle_bot_added_to_group(update, context)
                return

    # Check for license key in any chat (private or group)
    if message.text:
        license_key = extract_license_key(message.text)
        if license_key:
            await handle_license_key(message, context, license_key)
            return

    # Only handle group messages for the rest
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
    logger.info(f"About to call add_member: group_id={group_id}, user_id={user_id}, username={username}, first_name={first_name}")
    member, is_new = db.add_member(group_id, user_id, username, first_name, restrict_new=False)
    logger.info(f"add_member returned: member={member is not None}, is_new={is_new}, group_id={group_id}, user_id={user_id}")

    # Update member activity
    db.update_member_activity(group_id, user_id)

    # Check if user is admin first - admins are NEVER restricted and EXEMPT from all penalties
    member = db.get_member(group_id, user_id)
    logger.info(f"get_member returned: member={member is not None}, group_id={group_id}, user_id={user_id}")
    
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

            # Get undesignated slot response from bot settings
            admin_user_id = group_config.get("admin_user_id")
            bot_settings = db.get_bot_settings_for_group(admin_user_id, group_id) if admin_user_id else None
            undesignated_response = bot_settings.get("undesignated_slot_response", "Please only post during designated time slots.") if bot_settings else "Please only post during designated time slots."

            warning_msg = await safe_send_message(
                context=context, 
                chat_id=group_id,
                text=f"⏰ {first_name}, no active slot right now!\n"
                f"{undesignated_response}\n",
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

# Create message handlers
text_message_handler = MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_message)
photo_message_handler = MessageHandler(filters.PHOTO, handle_message)
video_message_handler = MessageHandler(filters.VIDEO, handle_message)
document_message_handler = MessageHandler(filters.Document.ALL, handle_message)
sticker_message_handler = MessageHandler(filters.Sticker.ALL, handle_message)
animation_message_handler = MessageHandler(filters.ANIMATION, handle_message)
voice_message_handler = MessageHandler(filters.VOICE, handle_message)
video_note_message_handler = MessageHandler(filters.VIDEO_NOTE, handle_message)