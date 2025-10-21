from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
import logging
import os
from datetime import datetime, time, timedelta
from pytz import timezone
from services import database_service as db
from db import get_db_connection, execute_query
from bot_utils import safe_send_message

logger = logging.getLogger(__name__)
ist = timezone("Asia/Kolkata")

async def check_and_announce_slots(context: ContextTypes.DEFAULT_TYPE):
    """Check for active slots and announce them to the user at regular intervals"""
    try:
        query = "SELECT group_id FROM groups_config"
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

                    # Unpin previous messages
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
                        await context.bot.delete_message(chat_id=group_id, message_id=int(pinned_message_id_str))
                        logger.info(f"Deleted slot announcement message in group {group_id}")
                    except Exception as e:
                        logger.warning(f"Could not delete slot message: {e}",exc_info=True)
                    
                    # Clear the state from the database since there's no active slot
                    db.set_runtime_state(group_id, "pinned_slot_id", None)
                    db.set_runtime_state(group_id, "pinned_slot_message_id", None)

    except Exception as e:
        logger.error(f"Error in check_and_announce_slots: {e}",exc_info=True)


async def check_inactive_users(context: ContextTypes.DEFAULT_TYPE):
    """Check for inactive users: warn at 3 days, kick temporarily at 4 days."""
    try:
        logger.info("Checking for inactive users...")

        # Gets all groups
        query = "SELECT group_id FROM groups_config"
        groups=execute_query(query, fetch=True)

        for group in groups:
            group_id = group["group_id"]

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
                    try:
                        # Send warning
                        await safe_send_message(
                            context=context, 
                            chat_id=group_id,
                            text=f"⚠️ {first_name}, you've been inactive for 3 days!\n"
                            f"Please participate in today's activities or you'll be removed tomorrow."
                            )

                        # Log warning
                        db.log_inactivity_warning(group_id, user_id, '3day', member)

                        logger.info(f"Warned 3-day inactive user {user_id} in group {group_id}")

                    except Exception as e:
                        logger.error(f"Error warning user {user_id}: {e}",exc_info=True)

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
                    logger.error(f"Error kicking user {user_id} from group {group_id}: {e}",exc_info=True)

    except Exception as e:
        logger.error(f"Error in check_inactive_users: {e}",exc_info=True)


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
        query = "SELECT group_id FROM groups_config"
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
                    warning_key = f"mid_slot_warn_{slot_id}_{datetime.now().date()}"
                    
                    # Check if warning has already been sent by checking the database
                    if not db.get_runtime_state(group_id, warning_key):
                        await safe_send_message(
                            context=context, 
                            chat_id=group_id,
                            text=f"⏰ *{slot_name}* - Final Reminder!\n\n"
                                 f"⚠️ Only 10 minutes remaining!\n"
                                 f"📸 If you haven't posted yet, do it now!",
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
    """Post leaderboard automatically at end of all the slots for the day."""
    try:
        # Get all group configs
        query = "SELECT group_id FROM groups_config"
        groups=execute_query(query, fetch=True)

        for group in groups:
            group_id = group["group_id"]

            # Get active event
            event = db.get_active_event(group_id)
            if not event: continue

            # Get leaderboard
            top_members = db.get_leaderboard(group_id, 10)

            if top_members:
                message = "🏆 **Leaderboard - Top 10**\n\n"

                for i, member in enumerate(top_members, 1):
                    name = member.get("first_name", member.get("username", "Unknown"))
                    earned = member.get("total_points", 0)
                    knockout = member.get("knockout_points", 0)
                    total = earned - knockout

                    medal = ""
                    if i == 1: medal = "🥇"
                    elif i == 2: medal = "🥈"
                    elif i == 3: medal = "🥉"

                    message += f"{medal} {i}. {name} :\n{total} points"
                    if knockout > 0: message += f" ({earned} earned - {knockout} lost)"
                    message += "\n"

                message += "\n📅 Great job everyone! See you tomorrow! 🌟"

                await safe_send_message(context=context, chat_id=group_id, text=message)
                logger.info(f"Posted daily leaderboard for group {group_id}")

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
        query = "SELECT group_id FROM groups_config"
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

            except Exception as e:
                logger.error(f"Could not sync admins for group {group_id}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Critical error in the admin synchronization job: {e}", exc_info=True)

def setup_jobs(application):
    """Setup periodic jobs."""
    job_queue = application.job_queue
    scheduler = application.job_queue.scheduler

    # Check and announce slots every minute
    job_queue.run_repeating(check_and_announce_slots, interval=60, first=0)

    # Check mid-slot warnings every minute
    job_queue.run_repeating(check_mid_slot_warnings, interval=60, first=30)
    
    # Runs 10s after startup, then hourly
    job_queue.run_repeating(sync_admin_status, interval=3600, first=10)

    # Check inactive users once daily at 22:00 (10 PM)
    scheduler.add_job(check_inactive_users, trigger='cron', hour=22, minute=0, timezone=ist, args=[application])

    # Check user day cycles daily at 23:15 (just before first slot)
    scheduler.add_job(check_user_day_cycles, trigger='cron', hour=9, minute=30, timezone=ist, args=[application])

    # Check low-point users daily at END OF DAY (23:00 - 11 PM)
    scheduler.add_job(check_low_points, trigger='cron', hour=23, minute=0, timezone=ist, args=[application])

    # Post daily leaderboard at 22:00 (10:00 PM)
    scheduler.add_job(post_daily_leaderboard, trigger='cron', hour=18, minute=40, timezone=ist, args=[application])

    # Checks daily for zero activity users after leaderboard gets posted
    scheduler.add_job(check_daily_participation, trigger='cron', hour=23, minute=30, timezone=ist, args=[application])
    
    logger.info("Scheduled jobs setup completed")
