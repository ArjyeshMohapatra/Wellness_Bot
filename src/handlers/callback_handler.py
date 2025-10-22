from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
import logging
from datetime import datetime
from services import database_service as db
from db import execute_query
from services.file_storage import FileStorage
import config
from pytz import timezone
from bot_utils import safe_send_message, safe_edit_message_text, safe_callback_reply_text

logger = logging.getLogger(__name__)
ist=timezone("Asia/Kolkata")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    user_id = query.from_user.id
    first_name = query.from_user.first_name

    await query.answer()
    data = query.data

    # Handle confirmation responses (Yes/No for keyword mismatch)
    if data.startswith("confirm_"): await handle_confirmation(update, context)

    # Handle water consumption buttons
    elif data.startswith("water_"): await handle_water_button(update, context)

    else: logger.warning(f"Unhandled callback data: {data}")


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Yes/No confirmation for slot responses."""
    query = update.callback_query
    data = query.data
    message = query.message
    user = query.from_user
    first_name = user.first_name
    username=user.username
    last_name=user.last_name

    # Parse callback data: confirm_yes/no_<slot_id>_<user_id>_<original_msg_id>
    parts = data.split("_")
    if len(parts) < 4:
        await safe_edit_message_text(
            context, 
            chat_id=query.message.chat_id, 
            message_id=query.message.message_id, 
            text="❌ Invalid confirmation.")
        return

    expected_user_id = int(parts[3])

    # Get pending confirmation data
    pending_confirmations = context.bot_data.get("pending_confirmations", {})
    confirmation_data = pending_confirmations.get(query.message.message_id)

    if not confirmation_data:
        await safe_edit_message_text(
            context, 
            chat_id=query.message.chat_id, 
            message_id=query.message.message_id, 
            text="⏱️ This confirmation has expired or already processed.")
        return

    # Verify it's the right user
    if query.from_user.id != expected_user_id:
        response_msg = await safe_callback_reply_text(query, context, text = f"{first_name}, this confirmation is not for you!")
        context.job_queue.run_once(lambda _: context.bot.delete_message(chat_id=response_msg.chat_id, message_id=response_msg.message_id),when=5)
        return

    context.bot_data["pending_confirmations"].pop(query.message.message_id, None)
    await query.answer()

    response = parts[1]  # 'yes' or 'no'
    slot_id = int(parts[2])

    group_id = confirmation_data["group_id"]
    slot_name = confirmation_data["slot_name"]
    event_id = confirmation_data["event_id"]
    points = confirmation_data["points"]
    content_type = confirmation_data.get("type", "text")
    username= confirmation_data["username"]
    first_name=confirmation_data["first_name"]
    last_name=confirmation_data["last_name"]
    caption = confirmation_data.get("caption", "")

    if response == "yes":
        display_name= username or first_name or "You"
        # Handle based on content type
        if content_type == "photo":
            photo_file_id = confirmation_data["photo_file_id"]

            # Get slot configuration to determine points
            slot = db.get_active_slot(group_id)
            if not slot:
                await safe_edit_message_text(
                    context, 
                    chat_id=query.message.chat_id, 
                    message_id=query.message.message_id, 
                    text="❌ No active slot found.")
                return

            points = slot["slot_points"]

            try:
                # Download and save photo
                file = await context.bot.get_file(photo_file_id)

                timestamp = datetime.now(ist).strftime("%Y_%m_%d_%I_%M_%S_%p").lower()
                filename = f"{username}_{slot_name}_{timestamp}.jpg"

                storage = FileStorage(config.STORAGE_PATH)
                local_path = await storage.save_photo(group_id, expected_user_id, username, slot_name, file, filename)

                # Award points
                db.add_points(group_id, expected_user_id, points, event_id)
                db.log_activity(group_id=group_id, user_id=expected_user_id, activity_type="photo", slot_name=slot_name,
                                telegram_file_id=photo_file_id, local_file_path=local_path, points_earned=points, is_valid=True,
                                username=username, first_name=first_name, last_name=last_name)

                if event_id: db.mark_slot_completed(group_id, event_id, slot_id, expected_user_id, "completed", points)

                await safe_edit_message_text(
                    context, 
                    chat_id=query.message.chat_id, 
                    message_id=query.message.message_id, 
                    text=f"✅ {display_name} scored {points} points!")
                logger.info(f"User {expected_user_id} confirmed photo for slot {slot_name}, awarded {points} points")

            except Exception as e:
                logger.error(f"Error saving confirmed photo: {e}",exc_info=True)
                await safe_edit_message_text(
                    context, 
                    chat_id=query.message.chat_id, 
                    message_id=query.message.message_id, 
                    text="❌ Error saving photo. Please try again.")

        elif content_type == "media":
            # Handle other media types (video, document, voice, etc.)
            file_id = confirmation_data["file_id"]
            media_type = confirmation_data.get("media_type", "media")
            file_ext = confirmation_data.get("file_ext", "file")

            # Get slot configuration to determine points
            slot = db.get_active_slot(group_id)
            if not slot:
                await safe_edit_message_text(
                    context, 
                    chat_id=query.message.chat_id, 
                    message_id=query.message.message_id, 
                    text="❌ No active slot found.")
                return

            # Determine points based on media type
            if media_type in ["video", "document","voice", "video_note", "sticker", "animation"]: points = slot["slot_points"]
            else: points = slot["slot_points"]

            try:
                # Download and save media
                file = await context.bot.get_file(file_id)

                timestamp = datetime.now(ist).strftime("%Y_%m_%d_%I_%M_%S_%p").lower()
                filename = f"{username}_{slot_name}_{timestamp}.{file_ext}"

                storage = FileStorage(config.STORAGE_PATH)
                local_path = await storage.save_media(group_id, expected_user_id, username, slot_name, file, filename, media_type)

                # Award points
                
                db.add_points(group_id, expected_user_id, points, event_id)
                if event_id and points > 0: db.mark_slot_completed(group_id, event_id, slot_id, expected_user_id, "completed", points)
                
                db.log_activity(group_id, expected_user_id, media_type, slot_name, message_content=caption, username=username, first_name=first_name,
                                last_name=last_name, telegram_file_id=file_id, local_file_path=local_path, points_earned=points, is_valid=True)


                points_msg = (f"scored {points} points!" if points > 0 else " no points.)")
                await safe_edit_message_text(
                    context, 
                    chat_id=query.message.chat_id, 
                    message_id=query.message.message_id, 
                    text=f"✅ {display_name} {points_msg}")
                logger.info(f"User {expected_user_id} confirmed {media_type} for slot {slot_name}, awarded {points} points")

            except Exception as e:
                logger.error(f"Error saving confirmed {media_type}: {e}",exc_info=True)
                await safe_edit_message_text(
                    context, 
                    chat_id=query.message.chat_id, 
                    message_id=query.message.message_id, 
                    text=f"❌ Error saving {media_type}. Please try again.")

        else:
            # Text confirmation
            text = confirmation_data.get("text", "")

            # Get slot configuration to determine points
            slot = db.get_active_slot(group_id)
            if not slot:
                await safe_edit_message_text(
                    context, 
                    chat_id=query.message.chat_id, 
                    message_id=query.message.message_id, 
                    text="❌ No active slot found.")
                return

            points = slot["slot_points"]

            db.add_points(group_id, expected_user_id, points, event_id)
            db.log_activity(group_id, expected_user_id, "text", slot_name, message_content=text, username=username, first_name=first_name,
                            last_name=last_name, points_earned=points, is_valid=True)

            if event_id: db.mark_slot_completed(group_id, event_id, slot_id, expected_user_id, "completed", points)

            await safe_edit_message_text(
                context, 
                chat_id=query.message.chat_id, 
                message_id=query.message.message_id, 
                text=f"✅ {display_name} scored {points} points!")
            logger.info(f"User {expected_user_id} confirmed text for slot {slot_name}, awarded {points} points")

    else:
        content_type = confirmation_data.get("type", "text")
        if content_type == "media":
            # If it's media, get the specific type like 'animation', 'video', etc.
            content_type = confirmation_data.get("media_type", "media")

        db.log_activity(group_id=group_id, user_id=expected_user_id, slot_name=slot_name, username=username, first_name=first_name, last_name=last_name,
                        activity_type=content_type, message_content=confirmation_data.get("text", ""), points_earned=0, is_valid=False)

        await safe_edit_message_text(
            context,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="❌ Cancelled. No points awarded.")
        logger.info(f"User {expected_user_id} rejected confirmation for slot {slot_name}")
        
        # Delete the original message that was rejected
        try:
            original_message_id = confirmation_data.get("original_message_id")
            if original_message_id:
                await context.bot.delete_message(chat_id=group_id, message_id=original_message_id)
                logger.info(f"Deleted rejected message {original_message_id}")
        except Exception as e:
            logger.warning(f"Could not delete original message: {e}",exc_info=True)

    async def delete_message(context: ContextTypes.DEFAULT_TYPE):
        """Awaits the message deletion coroutine."""
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Could not delete confirmation message: {e}",exc_info=True)

    context.job_queue.run_once(delete_message, when=3)


async def handle_water_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle water consumption button clicks (1L to 5L)."""
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    group_id = query.message.chat.id
    username=query.from_user.username
    last_name=query.from_user.last_name

    member = db.get_member(group_id, user_id)

    if member and member.get("is_restricted", 0) == 1:
        restriction_until = member.get("restriction_until")
        if restriction_until and datetime.now(ist) > restriction_until:
            query_text = "UPDATE group_members SET is_restricted = 0, restriction_until = NULL WHERE group_id = %s AND user_id = %s"
            execute_query(query_text, (group_id, user_id))
            logger.info(f"User {user_id}'s restriction has expired. Unrestricted in DB.")
        else:
            await query.answer("You are currently restricted and cannot perform this action.",show_alert=True)
            return
        await query.answer("You are currently restricted and cannot perform this action.",show_alert=True)

    # Parse: water_<liters>_<slot_id>
    parts = data.split("_")
    if len(parts) < 3:
        await query.answer("Invalid water selection", show_alert=True)
        return

    liters = int(parts[1])
    slot_id = int(parts[2])

    # Add in-memory lock to prevent spam clicking
    if "button_locks" not in context.bot_data: context.bot_data["button_locks"] = set()

    lock_key = f"{group_id}_{user_id}_{slot_id}_{datetime.now(ist).date()}"

    if lock_key in context.bot_data["button_locks"]:
        await query.answer("⏳ Processing your previous click, please wait...", show_alert=True)
        return

    # Acquire lock
    context.bot_data["button_locks"].add(lock_key)

    try:
        # Get slot info
        active_slot = db.get_active_slot(group_id)

        if not active_slot or active_slot["slot_id"] != slot_id:
            await query.answer("This water slot is no longer active!", show_alert=True)
            return

        # Get event
        event = db.get_active_event(group_id)
        event_id = event["event_id"] if event else None

        # Check if already completed today
        if event_id and db.check_slot_completed_today(event_id, slot_id, user_id):
            await query.answer("Already completed!", show_alert=True)
            # Send visible message in chat
            slot_name = active_slot["slot_name"]
            response_msg = await safe_send_message(
                context=context, 
                chat_id=group_id,
                text=f"⚠️ {first_name}, you have already completed {slot_name} slot for today!",
                reply_to_message_id=query.message.message_id,
            )
            # Auto-delete after 5 seconds
            context.job_queue.run_once(lambda ctx: response_msg.delete(), when=5)
            return

        points = active_slot["slot_points"]
        slot_name = active_slot["slot_name"]

        # Award points
        db.add_points(group_id, user_id, points, event_id)
        db.log_activity(group_id=group_id,  user_id=user_id,  activity_type="button",  slot_name=slot_name, 
                        message_content=f"{liters}L water", username=username, first_name=first_name, last_name=last_name, 
                        points_earned=points)
        if event_id:
            db.mark_slot_completed(group_id, event_id, slot_id, user_id, "completed", points)

        # Send confirmation to telegram
        await query.answer(f"✅ {liters}L logged! {points} points!", show_alert=True)

        # Send a separate message to show who completed (doesn't replace buttons)
        response_msg = await safe_send_message(context=context, chat_id=group_id, text=f"💧 {first_name} drank {liters}L of water! {points} points!")

        logger.info(f"User {user_id} logged {liters}L water for slot {slot_name}")

    finally:
        # Release lock after 5 seconds to prevent accidental double-clicks
        async def release_lock(ctx): context.bot_data["button_locks"].discard(lock_key)

        context.job_queue.run_once(release_lock, when=5)


callback_handler = CallbackQueryHandler(handle_callback)
