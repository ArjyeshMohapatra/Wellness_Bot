from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, ReplyKeyboardMarkup
import logging
import os
import json
from datetime import datetime, time, timedelta
from pytz import timezone
from ..services import database_service as db
from ..db import get_db_connection, execute_query
from ..bot_utils import safe_send_message

logger = logging.getLogger(__name__)
ist = timezone("Asia/Kolkata")

async def check_and_announce_slots(context: ContextTypes.DEFAULT_TYPE):
    """Check for active slots and announce them to the user at regular intervals"""
    try:
        query = "SELECT group_id FROM groups_config WHERE group_id != 0"
        groups = execute_query(query, fetch=True)

        for group in groups:
            group_id = group["group_id"]
            active_slot = db.get_active_slot(group_id)

            # Get the ID of the slot that is currently pinned from the database
            pinned_slot_id_str = db.get_runtime_state(group_id, "pinned_slot_id")

            if active_slot:
                slot_id = active_slot["slot_id"]
                
                # Check if the currently active slot is different from the one we have pinned
                if str(slot_id) != pinned_slot_id_str:
                    # This is a new slot, so we need to announce it.
                    slot_name = active_slot["slot_name"]
                    slot_type = active_slot["slot_type"]
                    start_time = active_slot["start_time"]
                    end_time = active_slot["end_time"]

                    # --- All of your existing message formatting logic remains the same ---
                    if hasattr(start_time, "total_seconds"): start_str = (datetime.min + start_time).strftime("%H:%M")
                    else:
                        start_str = (start_time.strftime("%H:%M") if hasattr(start_time, "strftime") else str(start_time))
                    if hasattr(end_time, "total_seconds"): end_str = (datetime.min + end_time).strftime("%H:%M")
                    else:
                        end_str = (end_time.strftime("%H:%M") if hasattr(end_time, "strftime") else str(end_time))
                    
                    message = f"⏰ {slot_name} - Time: {start_str} to {end_str}\n\n"
                    message += active_slot.get("initial_message", f"{slot_name} has started!")

                    slot_msg = None # Initialize slot_msg to None
                    if slot_type == "button":
                        # Use configured buttons from database
                        button_count = active_slot.get("button_count", 0)
                        button_names = json.loads(active_slot.get("button_names", "[]"))
                        button_values = json.loads(active_slot.get("button_values", "[]"))
                        
                        if button_count > 0 and button_names and button_values:
                            # Create keyboard with configured buttons
                            keyboard = []
                            buttons_per_row = 3  # Max 3 buttons per row
                            for i in range(0, len(button_names), buttons_per_row):
                                row = []
                                for j in range(buttons_per_row):
                                    if i + j < len(button_names):
                                        button_text = button_names[i + j]
                                        button_value = button_values[i + j] if i + j < len(button_values) else 0
                                        row.append(InlineKeyboardButton(
                                            button_text, 
                                            callback_data=f"button_{button_value}_{slot_id}"
                                        ))
                                if row:
                                    keyboard.append(row)
                        else:
                            # Fallback to default water buttons if no configuration
                            keyboard = [
                                [InlineKeyboardButton("1L 💧", callback_data=f"water_1_{slot_id}"),
                                 InlineKeyboardButton("2L 💧💧", callback_data=f"water_2_{slot_id}"),
                                 InlineKeyboardButton("3L 💧💧💧", callback_data=f"water_3_{slot_id}")],
                                [InlineKeyboardButton("4L 💧💧💧💧", callback_data=f"water_4_{slot_id}"),
                                 InlineKeyboardButton("5L 💧💧💧💧💧", callback_data=f"water_5_{slot_id}")]
                            ]
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        slot_msg = await safe_send_message(context=context ,chat_id=group_id, text=message, reply_markup=reply_markup)
                    else:
                        image_path = active_slot.get("image_file_path")
                        if image_path and os.path.exists(image_path):
                            with open(image_path, "rb") as photo:
                                slot_msg = await context.bot.send_photo(chat_id=group_id, photo=photo, caption=message)
                        else:
                            slot_msg = await safe_send_message(context=context, chat_id=group_id, text=message)
                    
                    # Unpin all pinned messages        
                    try:
                        await context.bot.unpin_all_chat_messages(group_id)
                        logger.info(f"Unpinned previous messages in group {group_id}")
                    except Exception as unpin_error:
                        logger.warning(f"Could not unpin previous messages: {unpin_error}")
                    
                    # Pin the new slot announcement
                    try:
                        await context.bot.pin_chat_message(group_id, slot_msg.message_id)
                        logger.info(f"Pinned slot {slot_name} announcement in group {group_id}")
                    except Exception as pin_error:
                        logger.warning(f"Could not pin slot announcement: {pin_error}")

                    # Save the new state to the database
                    db.set_runtime_state(group_id, "pinned_slot_id", str(slot_id))
                    db.set_runtime_state(group_id, "pinned_slot_message_id", str(slot_msg.message_id))
                    logger.info(f"Announced and saved state for slot {slot_name} in group {group_id}")
            
            else:
                # No active slot. Check if there is a pinned message that we need to clean up.
                pinned_message_id_str = db.get_runtime_state(group_id, "pinned_slot_message_id")
                if pinned_message_id_str:
                    
                    # A slot just ended. Log 'missed' for non-participants.
                    ended_slot_id_str = db.get_runtime_state(group_id, "pinned_slot_id")
                    active_event = db.get_active_event(group_id)
                    
                    if ended_slot_id_str and active_event:
                        try:
                            db.log_missed_slots(group_id, active_event['event_id'], int(ended_slot_id_str))
                        except Exception as e:
                            logger.error(f"Failed to log missed slots: {e}", exc_info=True)
                            
                    try:
                        # Unpin all messages first
                        await context.bot.unpin_all_chat_messages(group_id)
                        logger.info(f"Unpinned all messages in group {group_id} after slot end")
                        
                        # Then delete the specific slot message
                        await context.bot.delete_message(chat_id=group_id, message_id=int(pinned_message_id_str))
                        logger.info(f"Deleted slot announcement message {pinned_message_id_str} in group {group_id}")
                    except Exception as e:
                        logger.warning(f"Could not unpin/delete slot message: {e}",exc_info=True)
                    
                    # Clear the state from the database since there's no active slot
                    db.set_runtime_state(group_id, "pinned_slot_id", None)
                    db.set_runtime_state(group_id, "pinned_slot_message_id", None)

    except Exception as e:
        logger.error(f"Error in check_and_announce_slots: {e}",exc_info=True)


async def check_inactive_users(context: ContextTypes.DEFAULT_TYPE):
    """Check for inactive users: warn at 3 days, kick temporarily at 4 days."""
    logger.info("Checking for inactive users...")
    groups = []
    try:
        query = "SELECT group_id FROM groups_config WHERE group_id != 0"
        groups = execute_query(query, fetch=True)
    except Exception as e:
        logger.error(f"CRITICAL: Failed to fetch groups for inactivity check: {e}", exc_info=True)
        return

    for group in groups:
        group_id = group["group_id"]
        try:
            # Check for 3-day inactive (warning)
            inactive_3day = db.get_inactive_members(group_id, 3)
            for member in inactive_3day:
                user_id = member["user_id"]
                first_name = member.get("first_name", "User")
                last_name = member.get("last_name","")
                username = member.get("username","User")

                # Check if already warned today
                query = """
                    SELECT * FROM inactivity_warnings 
                    WHERE group_id = %s AND user_id = %s AND warning_date = CURDATE() AND warning_type = '3day'
                """
                existing= execute_query(query,(group_id,user_id), fetch=True)

                if not existing:
                    # Send warning
                    await safe_send_message(
                        context=context, 
                        chat_id=group_id,
                        text=f"⚠️ {first_name}, you've been inactive for 3 days!\nPlease participate in today's activities or you'll be removed tomorrow."
                        )
                    try:
                        # Log warning
                        db.log_inactivity_warning(group_id, user_id, '3day', member)
                        logger.info(f"Warned 3-day inactive user {user_id} in group {group_id}")
                    except Exception as e:
                        logger.error(f"Error warning user {user_id} in group {group_id}: {e}", exc_info=True)

            # Check for 4-day inactive (kick temporarily)
            inactive_4day = db.get_inactive_members(group_id, 4)
            for member in inactive_4day:
                user_id = member["user_id"]
                first_name = member.get("first_name", "User")

                try:
                    # Deduct 20 knockout points for 4-day inactivity before kicking
                    db.deduct_knockout_points(group_id, user_id, 20)
                    await context.bot.ban_chat_member(group_id, user_id)
                    # Remove from database
                    db.remove_member(group_id, user_id, "kicked")
                    await context.bot.unban_chat_member(group_id, user_id)
                    # Send notification
                    await safe_send_message(
                        context=context,
                        chat_id=group_id,
                        text=f"🚫 {first_name} has been removed from the group due to 4 days of inactivity.\n"
                    )

                    logger.info(f"Kicked 4-day inactive user {user_id} from group {group_id}")
                except Exception as e:
                    logger.error(f"Error kicking user {user_id} from group {group_id}: {e}", exc_info=True)

        except Exception as group_e:
            logger.error(f"Failed to process inactivity check for group {group_id}: {group_e}", exc_info=True)


async def check_low_points(context: ContextTypes.DEFAULT_TYPE):
    """Check for users with low points and kick them."""
    try:
        logger.info("Checking for low-point users...")

        # Get all active events
        query = """
            SELECT e.event_id, e.group_id, e.min_pass_points
            FROM events e
            WHERE e.is_active = TRUE
        """
        events=execute_query(query)

        for event in events:
            group_id = event["group_id"]
            min_points = event["min_pass_points"]

            if min_points <= 0: continue

            # Get members who COMPLETED 7 days but are below minimum
            query = """
                SELECT user_id, username, first_name, total_points, user_day_number
                FROM group_members
                WHERE group_id = %s 
                AND total_points < %s 
                AND user_day_number >= 7
                AND is_restricted = 0
            """

            low_point_members=execute_query(query,(group_id,min_points),fetch=True)

            for member in low_point_members:
                user_id = member["user_id"]
                first_name = member.get("first_name", "User")
                username=member.get("username","User")
                last_name=member.get("last_name","")
                total_points = member["total_points"]

                try:
                    await context.bot.ban_chat_member(group_id, user_id)

                    # Remove from database
                    db.remove_member(group_id, user_id, "kicked")
                    
                    await context.bot.unban_chat_member(group_id,user_id)

                    await safe_send_message(
                        context=context, 
                        chat_id=group_id,
                        text=f"👋 {first_name}, thank you for your participation!\n"
                        f"🎯 You completed 7 days and earned {total_points} points!\n\n"
                        f"Unfortunately, you didn't reach the minimum {min_points} points required.\n"
                        f"💪 Keep trying!"
                    )

                    logger.info(f"Kicked low-point user {user_id} from group {group_id} after 7 days with {total_points} points")

                except Exception as e:
                    logger.error(f"Error kicking user {user_id}: {e}",exc_info=True)

    except Exception as e:
        logger.error(f"Error in check_low_points: {e}",exc_info=True)
        

async def check_mid_slot_warnings(context: ContextTypes.DEFAULT_TYPE):
    """Post warning messages at last 10 mins of slot duration."""
    try:
        query = "SELECT group_id FROM groups_config WHERE group_id != 0"
        groups = execute_query(query, fetch=True)

        for group in groups:
            group_id = group["group_id"]
            active_slot = db.get_active_slot(group_id)

            if active_slot:
                slot_id = active_slot["slot_id"]
                slot_name = active_slot["slot_name"]
                end_time = active_slot["end_time"]

                if hasattr(end_time, "total_seconds"):
                    end_time = (datetime.min + end_time).time()

                now = datetime.now(ist).time()
                end_datetime = datetime.combine(datetime.today(), end_time)
                reminder_datetime = end_datetime - timedelta(minutes=10)
                reminder_time = reminder_datetime.time()

                if now.hour == reminder_time.hour and now.minute == reminder_time.minute:
                    # Use a unique key for today's warning for this specific slot
                    warning_key = f"mid_slot_warn_{slot_id}_{datetime.now(ist).date()}"
                    
                    # Check if warning has already been sent by checking the database
                    if not db.get_runtime_state(group_id, warning_key):
                        await safe_send_message(
                            context=context, 
                            chat_id=group_id,
                            text=f"⏰ *{slot_name}* - Final Reminder!\n\n"
                                 f"⚠️ Only 10 minutes remaining!\n",
                            parse_mode="Markdown",
                        )

                        db.set_runtime_state(group_id, warning_key, "sent")
                        logger.info(f"Sent mid-slot warning for {slot_name} in group {group_id}")
    except Exception as e:
        logger.error(f"Error in check_mid_slot_warnings: {e}",exc_info=True)


async def check_user_day_cycles(context: ContextTypes.DEFAULT_TYPE):
    """Check and update user day cycles, and reset after Day 7."""
    try:
        logger.info("Checking user day cycles...")

        # Get all groups
        query = "SELECT group_id FROM groups_config"
        groups=execute_query(query, fetch=True)

        for group in groups:
            group_id = group["group_id"]

            # Get all members in this group
            query = """
                SELECT user_id, username, first_name, last_name, user_day_number, cycle_start_date, 
                       is_restricted, total_points
                FROM group_members
                WHERE group_id = %s
            """
            members=execute_query(query,(group_id,), fetch=True)

            for member in members:
                user_id = member["user_id"]
                first_name = member.get("first_name", "User")
                username=member.get("username","User")
                last_name=member.get("last_name","")
                day_number = member["user_day_number"]
                cycle_start = member["cycle_start_date"]
                is_restricted = member["is_restricted"]
                total_points = member["total_points"]

                if not cycle_start:
                    continue

                # Calculate days since cycle start
                today = datetime.now(ist).date()
                days_elapsed = (today - cycle_start).days

                # Update day number if it's a new day (for non-restricted users)
                if not is_restricted and days_elapsed > 0:
                    new_day = days_elapsed + 1

                    if new_day == day_number: continue

                    if new_day > 7:
                        # Reset the 7-day cycle
                        query = """
                            UPDATE group_members 
                            SET user_day_number = 1, 
                                cycle_start_date = CURDATE(),
                                total_points = 0,
                                knockout_points = 0
                            WHERE group_id = %s AND user_id = %s
                        """
                        execute_query(query,(group_id,user_id))

                        try:
                            await safe_send_message(
                                context=context, 
                                chat_id=group_id,
                                text=f"🎊 {first_name}, congratulations!\n\n"
                                f"You completed your 7-day wellness cycle with {total_points} points! 🏆\n\n"
                                f"🔄 Starting a fresh Day 1 cycle.\n"
                                f"Your points have been reset. Let's go again! 💪",
                            )
                            logger.info(f"Reset 7-day cycle for user {user_id} in group {group_id}")
                        except Exception as e:
                            logger.error(f"Error sending cycle reset message: {e}",exc_info=True)

                    else:
                        # Just advance the day
                        query = "UPDATE group_members SET user_day_number = %s WHERE group_id = %s AND user_id = %s"
                        execute_query(query,(new_day, group_id, user_id))

                        logger.info(f"Advanced user {user_id} in group {group_id} to Day {new_day}")

    except Exception as e:
        logger.error(f"Error in check_user_day_cycles: {e}",exc_info=True)


async def post_daily_leaderboard(context: ContextTypes.DEFAULT_TYPE):
    """Post leaderboard automatically at configured leaderboard time for each group."""
    try:
        # Get all group configs (excluding group_id 0)
        query = "SELECT group_id FROM groups_config WHERE group_id != 0"
        groups=execute_query(query, fetch=True)

        for group in groups:
            group_id = group["group_id"]
            
            # Get group config to check leaderboard_time
            group_config = db.get_group_config(group_id)
            if not group_config:
                continue
                
            leaderboard_time = group_config.get('leaderboard_time')
            if not leaderboard_time:
                # Default to 22:00 if not set
                leaderboard_time = '22:00'
            
            # Check if current time matches the configured leaderboard time
            now = datetime.now(ist)
            current_time = now.strftime('%H:%M')
            
            if current_time != leaderboard_time:
                logger.debug(f"Skipping leaderboard for group {group_id}: current time {current_time} != configured time {leaderboard_time}")
                continue

            # Get active event
            event = db.get_active_event(group_id)
            if not event: continue

            # Get leaderboard
            top_members = db.get_leaderboard(group_id, 10)

            if top_members:
                message = "🏆 Leaderboard - Top 10\n\n"

                for i, member in enumerate(top_members, 1):
                    name = member.get("first_name", member.get("username", "Unknown"))
                    earned = member.get("total_points", 0)
                    knockout = member.get("knockout_points", 0)
                    total = earned - knockout

                    medal = ""
                    if i == 1: medal = "🥇"
                    elif i == 2: medal = "🥈"
                    elif i == 3: medal = "🥉"

                    message += f"{medal} {i}. {name} : {total} pts\n"
                    if knockout > 0: message += f" ({earned} earned - {knockout} lost)\n"
                    message += "\n"

                message += "\n📅 Great job everyone! See you tomorrow! 🌟"

                await safe_send_message(context=context, chat_id=group_id, text=message)
                logger.info(f"Posted daily leaderboard for group {group_id}")
                
                try:
                    await context.bot.pin_chat_message(group_id, message.message_id)
                    logger.info(f"Pinned Leaderboard announcement in group {group_id}")
                except Exception as pin_error:
                    logger.warning(f"Could not pin Leaderboard announcement: {pin_error}", exc_info=True)

    except Exception as e:
        logger.error(f"Error in post_daily_leaderboard: {e}",exc_info=True)

async def check_daily_participation(context: ContextTypes.DEFAULT_TYPE):
    """Checks for users with zero points for the day and applies a penalty."""
    try:
        logger.info("Checking for zero-participation members...")
        query="""
        SELECT group_id, event_id from events WHERE is_active=TRUE
        """
        events=execute_query(query,fetch=True)
        for event in events:
            group_id=event['group_id']
            event_id=event['event_id']
            
            db.penalize_zero_activity_members(group_id, event_id, 10)
            logger.info("Penalized non-restricted inactive members for the day.")
    except Exception as e:
        logger.error(f"Error in check_daily_participation job: {e}",exc_info=True)

async def sync_admin_status(context: ContextTypes.DEFAULT_TYPE):
    """Periodically fetches the list of admins for each group and updates the database."""
    logger.info("Running hourly job to synchronize admin statuses...")
    try:
        # Only sync groups that have a valid group_id (not NULL and not 0)
        query = "SELECT group_id FROM groups_config WHERE group_id IS NOT NULL AND group_id != 0"
        groups = execute_query(query, fetch=True)

        for group in groups:
            group_id = group["group_id"]
            try:
                # Get the list of admins directly from the Telegram API
                administrators = await context.bot.get_chat_administrators(group_id)
                # Extract just the user IDs from the list of ChatMember objects
                admin_user_ids = [admin.user.id for admin in administrators]

                # Update the database in a single, efficient transaction
                db.update_admin_status(group_id, admin_user_ids)

                # Check if bot is admin and needs license setup
                bot_is_admin = context.bot.id in admin_user_ids
                logger.info(f"Group {group_id}: bot_is_admin={bot_is_admin}")
                if bot_is_admin:
                    group_config = db.get_group_config(group_id)
                    logger.info(f"Group {group_id}: group_config exists={group_config is not None}")
                    
                    if not group_config:
                        # No config exists, create it
                        owner = next((admin for admin in administrators if admin.status == "creator"), None)
                        admin_user_id = owner.user.id if owner else administrators[0].user.id if administrators else None
                        if admin_user_id:
                            success = db.create_group_config(group_id, admin_user_id)
                            logger.info(f"Group {group_id}: created config={success}")
                            if success:
                                group_config = db.get_group_config(group_id)
                                logger.info(f"Group {group_id}: new config created")
                    
                    if group_config:
                        event_id = group_config.get('event_id')
                        logger.info(f"Group {group_id}: event_id='{event_id}'")
                    
                    if group_config and not group_config.get('event_id'):
                        # Bot is admin but no event/license assigned - trigger license request
                        logger.info(f"Bot is admin in group {group_id} but no event/license found - requesting license")
                        from .join_handler import handle_bot_promoted_to_admin
                        
                        # Create a mock update object for the handler
                        class MockUpdate:
                            def __init__(self, chat_id):
                                self.effective_chat = type('Chat', (), {'id': chat_id})()
                        
                        mock_update = MockUpdate(group_id)
                        await handle_bot_promoted_to_admin(mock_update, context)

            except Exception as e:
                logger.error(f"Could not sync admins for group {group_id}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Critical error in the admin synchronization job: {e}", exc_info=True)


async def sync_group_info(context: ContextTypes.DEFAULT_TYPE):
    """Sync group names and admin permissions for all active groups"""
    try:
        logger.info("Starting group info sync job")

        # Get all groups with active events
        query = """
            SELECT DISTINCT gc.group_id, gc.admin_user_id, gc.event_id
            FROM groups_config gc
            WHERE gc.event_id IS NOT NULL AND gc.group_id != 0 AND gc.is_active = TRUE
        """
        groups = execute_query(query, fetch=True)

        for group in groups:
            group_id = group["group_id"]
            try:
                # Get current group info from Telegram
                chat_info = await context.bot.get_chat(group_id)
                group_name = chat_info.title or f"Group {group_id}"

                # Check if bot has admin permissions
                has_admin_permissions = False
                try:
                    bot_member = await context.bot.get_chat_member(group_id, context.bot.id)
                    has_admin_permissions = bot_member.status in ["administrator", "creator"]
                except Exception as e:
                    logger.warning(f"Could not check bot permissions for group {group_id}: {e}")

                # Update group name and admin permissions in database
                update_query = """
                    UPDATE groups_config
                    SET group_name = %s, has_admin_permissions = %s
                    WHERE group_id = %s
                """
                execute_query(update_query, (group_name, has_admin_permissions, group_id))

                logger.info(f"Updated group {group_id}: name='{group_name}', admin_permissions={has_admin_permissions}")

            except Exception as e:
                logger.error(f"Could not sync info for group {group_id}: {e}", exc_info=True)

        logger.info("Group info sync job completed")

    except Exception as e:
        logger.error(f"Critical error in group info sync job: {e}", exc_info=True)


async def refresh_bot_settings(context: ContextTypes.DEFAULT_TYPE):
    """Refresh bot settings cache for all active groups"""
    try:
        logger.info("Starting bot settings refresh job")

        # Get all groups with active events
        query = """
            SELECT DISTINCT gc.group_id, gc.event_id
            FROM groups_config gc
            WHERE gc.event_id IS NOT NULL AND gc.group_id != 0 AND gc.is_active = TRUE
        """
        groups = execute_query(query, fetch=True)

        refreshed_count = 0
        for group in groups:
            group_id = group["group_id"]
            event_id = group["event_id"]

            try:
                # Get latest settings from database
                settings = db.get_bot_settings_for_event(event_id)
                if settings:
                    # Update any cached settings or perform validation
                    logger.info(f"Refreshed settings for group {group_id}, event {event_id}")
                    refreshed_count += 1
                else:
                    logger.warning(f"No settings found for group {group_id}, event {event_id}")

            except Exception as e:
                logger.error(f"Could not refresh settings for group {group_id}: {e}", exc_info=True)

        logger.info(f"Bot settings refresh job completed - refreshed {refreshed_count} groups")

    except Exception as e:
        logger.error(f"Critical error in bot settings refresh job: {e}", exc_info=True)


async def handle_sync_notification(event_id: int, change_type: str, context: ContextTypes.DEFAULT_TYPE):
    """Handle real-time sync notifications from admin panel"""
    try:
        logger.info(f"Handling sync notification: event_id={event_id}, change_type={change_type}")

        if change_type == 'settings_updated':
            # Find all groups using this event and refresh their info
            query = "SELECT group_id FROM groups_config WHERE event_id = %s AND is_active = TRUE"
            groups = execute_query(query, (event_id,), fetch=True)

            for group in groups:
                group_id = group['group_id']
                try:
                    # Update group name and permissions immediately
                    chat_info = await context.bot.get_chat(group_id)
                    group_name = chat_info.title or f"Group {group_id}"

                    has_admin_permissions = False
                    try:
                        bot_member = await context.bot.get_chat_member(group_id, context.bot.id)
                        has_admin_permissions = bot_member.status in ["administrator", "creator"]
                    except Exception as e:
                        logger.warning(f"Could not check bot permissions for group {group_id}: {e}")

                    # Update database
                    update_query = """
                        UPDATE groups_config
                        SET group_name = %s, has_admin_permissions = %s
                        WHERE group_id = %s
                    """
                    execute_query(update_query, (group_name, has_admin_permissions, group_id))

                    logger.info(f"Immediate sync completed for group {group_id} after {change_type}")

                except Exception as e:
                    logger.error(f"Could not sync group {group_id} immediately: {e}", exc_info=True)

        logger.info(f"Sync notification handling completed for {change_type}")

    except Exception as e:
        logger.error(f"Error handling sync notification: {e}", exc_info=True)


async def send_event_update_message(context, group_id, change_type):
    """Send event update notification to a group."""
    try:
        message_text = {
            'event_created': "📅 New event slot has been configured in the admin panel!",
            'event_updated': "📅 Event slot configuration has been updated in the admin panel!",
            'event_deleted': "📅 Event slot has been removed from the admin panel!"
        }.get(change_type, "📅 Event configuration has been updated!")

        await context.bot.send_message(
            chat_id=group_id,
            text=message_text,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Failed to send event update message to group {group_id}: {e}")


async def send_settings_update_message(context, group_id):
    """Send settings update notification to a group."""
    try:
        await context.bot.send_message(
            chat_id=group_id,
            text="⚙️ Bot settings have been updated in the admin panel!",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Failed to send settings update message to group {group_id}: {e}")


async def send_group_config_update_message(context, group_id):
    """Send group config update notification to a group."""
    try:
        await context.bot.send_message(
            chat_id=group_id,
            text="🔧 Group configuration has been updated in the admin panel!",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Failed to send group config update message to group {group_id}: {e}")


async def process_sync_notifications(context):
    """Process queued sync notifications and send real-time updates to affected groups."""
    try:
        # Get unprocessed notifications
        query = """
            SELECT id, change_type, event_id, admin_user_id, created_at
            FROM sync_notifications
            WHERE processed = FALSE
            ORDER BY created_at ASC
        """
        notifications = execute_query(query, fetch=True)

        if not notifications:
            return

        logger.info(f"Processing {len(notifications)} sync notifications")

        for notification in notifications:
            notification_id = notification['id']
            change_type = notification['change_type']
            event_id = notification['event_id']
            admin_user_id = notification['admin_user_id']

            try:
                # Find affected groups
                affected_groups = []
                if event_id:
                    # Event-related notification - find all groups using this event
                    groups_query = """
                        SELECT DISTINCT group_id
                        FROM events_slots
                        WHERE event_id = %s
                    """
                    group_results = execute_query(groups_query, (event_id,), fetch=True)
                    affected_groups = [row['group_id'] for row in group_results]
                else:
                    # Global notification - affect all groups
                    groups_query = "SELECT group_id FROM groups_config"
                    group_results = execute_query(groups_query, fetch=True)
                    affected_groups = [row['group_id'] for row in group_results]

                # Send real-time updates to affected groups
                for gid in affected_groups:
                    try:
                        if change_type in ['event_created', 'event_updated', 'event_deleted']:
                            # Refresh event slots for this group
                            await send_event_update_message(context, gid, change_type)
                        elif change_type in ['settings_updated']:
                            # Refresh bot settings
                            await send_settings_update_message(context, gid)
                        elif change_type in ['group_config_updated']:
                            # Refresh group configuration
                            await send_group_config_update_message(context, gid)

                        logger.info(f"Sent {change_type} update to group {gid}")

                    except Exception as e:
                        logger.error(f"Failed to send {change_type} update to group {gid}: {e}")

                # Mark notification as processed
                update_query = "UPDATE sync_notifications SET processed = TRUE WHERE id = %s"
                execute_query(update_query, (notification_id,))

            except Exception as e:
                logger.error(f"Error processing notification {notification_id}: {e}")

        logger.info("Sync notification processing completed")

    except Exception as e:
        logger.error(f"Error in process_sync_notifications: {e}", exc_info=True)


def setup_jobs(application):
    """Setup periodic jobs."""
    job_queue = application.job_queue
    scheduler = application.job_queue.scheduler

    # Check and announce slots every minute
    job_queue.run_repeating(check_and_announce_slots, interval=10, first=0)

    # Check mid-slot warnings every minute
    job_queue.run_repeating(check_mid_slot_warnings, interval=60, first=30)
    
    # Runs 10s after startup, then hourly
    job_queue.run_repeating(sync_admin_status, interval=10, first=10)

    # Sync group info (names, permissions) every 30 minutes
    job_queue.run_repeating(sync_group_info, interval=50, first=25)

    # Refresh bot settings every 15 minutes
    job_queue.run_repeating(refresh_bot_settings, interval=60, first=30)

    # Process sync notifications every 30 seconds for real-time updates
    job_queue.run_repeating(process_sync_notifications, interval=30, first=15)

    # Check inactive users once daily at 22:00 (10 PM)
    scheduler.add_job(check_inactive_users, trigger='cron', hour=12, minute=20, timezone=ist, args=[application])

    # Check user day cycles daily at 23:15 (just before first slot)
    scheduler.add_job(check_user_day_cycles, trigger='cron', hour=7, minute=30, timezone=ist, args=[application])

    # Check low-point users daily at END OF DAY (23:00 - 11 PM)
    scheduler.add_job(check_low_points, trigger='cron', hour=12, minute=15, timezone=ist, args=[application])

    # Post daily leaderboard at configured time (check every minute)
    job_queue.run_repeating(post_daily_leaderboard, interval=60, first=60)

    # Checks daily for zero activity users after leaderboard gets posted
    scheduler.add_job(check_daily_participation, trigger='cron', hour=12, minute=25, timezone=ist, args=[application])
    
    logger.info("Scheduled jobs setup completed")
