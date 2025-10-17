from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
import logging
import os
from datetime import datetime, time, timedelta
from pytz import timezone

from services import database_service as db
from db import get_db_connection, execute_query

logger = logging.getLogger(__name__)

# Track active slots to avoid duplicate announcements
active_slot_announcements = {}


async def check_and_announce_slots(context: ContextTypes.DEFAULT_TYPE):
    """Check for active slots and announce them to the user at regular intervals"""
    try:
        # Get all group configs
        query = "SELECT group_id FROM groups_config"
        groups=execute_query(query, fetch=True)

        for group in groups:
            group_id = group["group_id"]

            # Get active slot
            active_slot = db.get_active_slot(group_id)

            if active_slot:
                slot_id = active_slot["slot_id"]
                slot_name = active_slot["slot_name"]
                slot_type = active_slot["slot_type"]
                start_time = active_slot["start_time"]
                end_time = active_slot["end_time"]

                if active_slot_announcements.get(group_id) != slot_id:
                    if hasattr(start_time, "total_seconds"):
                        start_str = (datetime.min + start_time).strftime("%H:%M")
                    else:
                        start_str = (
                            start_time.strftime("%H:%M")
                            if hasattr(start_time, "strftime")
                            else str(start_time)
                        )

                    if hasattr(end_time, "total_seconds"):
                        end_str = (datetime.min + end_time).strftime("%H:%M")
                    else:
                        end_str = (
                            end_time.strftime("%H:%M")
                            if hasattr(end_time, "strftime")
                            else str(end_time)
                        )

                    # Build message with time
                    message = f"⏰ {slot_name} - Time: {start_str} to {end_str}\n\n"
                    message += active_slot.get(
                        "initial_message", f"{slot_name} has started!"
                    )

                    # For water slots with buttons
                    if slot_type == "button":
                        keyboard = [
                            [
                                InlineKeyboardButton(
                                    "1L 💧", callback_data=f"water_1_{slot_id}"
                                ),
                                InlineKeyboardButton(
                                    "2L 💧💧", callback_data=f"water_2_{slot_id}"
                                ),
                                InlineKeyboardButton(
                                    "3L 💧💧💧", callback_data=f"water_3_{slot_id}"
                                ),
                            ],
                            [
                                InlineKeyboardButton(
                                    "4L 💧💧💧💧", callback_data=f"water_4_{slot_id}"
                                ),
                                InlineKeyboardButton(
                                    "5L 💧💧💧💧💧", callback_data=f"water_5_{slot_id}"
                                ),
                            ],
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        slot_msg = await context.bot.send_message(
                            chat_id=group_id, text=message, reply_markup=reply_markup
                        )
                    else:
                        image_path = active_slot.get("image_file_path")

                        if image_path and os.path.exists(image_path):
                            with open(image_path, "rb") as photo:
                                slot_msg = await context.bot.send_photo(
                                    chat_id=group_id, photo=photo, caption=message
                                )
                        else:
                            slot_msg = await context.bot.send_message(
                                chat_id=group_id, text=message
                            )

                    # Unpin all previous messages before pinning new slot
                    try:
                        await context.bot.unpin_all_chat_messages(group_id)
                        logger.info(f"Unpinned previous messages in group {group_id}")
                    except Exception as unpin_error:
                        logger.warning(
                            f"Could not unpin previous messages: {unpin_error}"
                        )

                    # Pin the slot announcement
                    try:
                        await context.bot.pin_chat_message(
                            group_id, slot_msg.message_id
                        )
                        logger.info(
                            f"Pinned slot {slot_name} announcement in group {group_id}"
                        )
                    except Exception as pin_error:
                        logger.warning(f"Could not pin slot announcement: {pin_error}")

                    active_slot_announcements[group_id] = slot_id
                    logger.info(
                        f"Announced and pinned slot {slot_name} in group {group_id}"
                    )

            else:
                # No active slot
                if group_id in active_slot_announcements:
                    del active_slot_announcements[group_id]

    except Exception as e:
        logger.error(f"Error in check_and_announce_slots: {e}")


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
                        await context.bot.send_message(
                            chat_id=group_id,
                            text=f"⚠️ {first_name}, you've been inactive for 3 days!\n"
                            f"Please participate in today's activities or you'll be removed tomorrow.",
                        )

                        # Log warning
                        db.log_inactivity_warning(group_id, user_id, '3day', member)

                        logger.info(
                            f"Warned 3-day inactive user {user_id} in group {group_id}"
                        )

                    except Exception as e:
                        logger.error(f"Error warning user {user_id}: {e}")

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
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=f"🚫 {first_name} has been removed from the group due to 4 days of inactivity.\n"
                    )

                    logger.info(f"Kicked 4-day inactive user {user_id} from group {group_id}")

                except Exception as e:
                    logger.error(f"Error kicking user {user_id} from group {group_id}: {e}")

    except Exception as e:
        logger.error(f"Error in check_inactive_users: {e}")


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

            if min_points <= 0:
                continue

            # Get members who COMPLETED 7 days but are below minimum
            query = """
                SELECT user_id, username, first_name, current_points, user_day_number
                FROM group_members
                WHERE group_id = %s 
                AND current_points < %s 
                AND user_day_number >= 7
                AND is_restricted = 0
            """

            low_point_members=execute_query(query,(group_id,min_points),fetch=True)

            for member in low_point_members:
                user_id = member["user_id"]
                first_name = member.get("first_name", "User")
                username=member.get("username","User")
                last_name=member.get("last_name","")
                current_points = member["current_points"]

                try:
                    # Kick the user temporarily (1 day)
                    until_date = datetime.now() + timedelta(days=1)
                    await context.bot.ban_chat_member(
                        group_id, user_id, until_date=until_date
                    )

                    # Remove from database
                    db.remove_member(group_id, user_id, "kicked")

                    await context.bot.send_message(
                        chat_id=group_id,
                        text=f"👋 {first_name}, thank you for your participation!\n"
                        f"🎯 You completed 7 days and earned {current_points} points!\n\n"
                        f"Unfortunately, you didn't reach the minimum {min_points} points required.\n"
                        f"💪 Keep trying!"
                    )

                    logger.info(
                        f"Kicked low-point user {user_id} from group {group_id} after 7 days with {current_points} points"
                    )

                except Exception as e:
                    logger.error(f"Error kicking user {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error in check_low_points: {e}")


# Track mid-slot warnings already sent
mid_slot_warnings_sent = {}


async def check_mid_slot_warnings(context: ContextTypes.DEFAULT_TYPE):
    """Post warning messages at last 10 mins of slot duration."""
    try:
        # Gets all groups
        query = "SELECT group_id FROM groups_config"
        groups=execute_query(query, fetch=True)

        for group in groups:
            group_id = group["group_id"]

            # Get active slot
            active_slot = db.get_active_slot(group_id)

            if active_slot:
                slot_id = active_slot["slot_id"]
                slot_name = active_slot["slot_name"]
                end_time = active_slot["end_time"]

                # Convert timedelta to datetime if needed
                if hasattr(end_time, "total_seconds"):
                    end_time = (datetime.min + end_time).time()

                # Calculate slot duration and mid-point
                now = datetime.now().time()

                end_datetime = datetime.combine(datetime.today(), end_time)
                reminder_datetime = end_datetime - timedelta(minutes=10)
                reminder_time = reminder_datetime.time()

                # Check if its the reminder time
                if (
                    now.hour == reminder_time.hour
                    and now.minute == reminder_time.minute
                ):

                    # Check if warning already sent for this slot today
                    today_key = f"{group_id}_{slot_id}_{datetime.now().date()}"

                    if today_key not in mid_slot_warnings_sent:
                        await context.bot.send_message(
                            chat_id=group_id,
                            text=f"⏰ *{slot_name}* - Final Reminder!\n\n"
                            f"⚠️ Only 10 minutes remaining!\n"
                            f"📸 If you haven't posted yet, do it now!",
                            parse_mode="Markdown",
                        )

                        mid_slot_warnings_sent[today_key] = True
                        logger.info(
                            f"Sent mid-slot warning for {slot_name} in group {group_id}"
                        )

            else:
                # Clear warnings if no active slot
                keys_to_remove = [
                    k
                    for k in mid_slot_warnings_sent.keys()
                    if k.startswith(f"{group_id}_")
                ]
                for key in keys_to_remove:
                    del mid_slot_warnings_sent[key]

    except Exception as e:
        logger.error(f"Error in check_mid_slot_warnings: {e}")


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
                       is_restricted, current_points
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
                current_points = member["current_points"]

                if not cycle_start:
                    continue

                # Calculate days since cycle start
                today = datetime.now().date()
                days_elapsed = (today - cycle_start).days

                # Update day number if it's a new day (for non-restricted users)
                if not is_restricted and days_elapsed > 0:
                    new_day = days_elapsed + 1

                    if new_day == day_number:
                        continue

                    if new_day > 7:
                        # Reset the 7-day cycle
                        query = """
                            UPDATE group_members 
                            SET user_day_number = 1, 
                                cycle_start_date = CURDATE(),
                                current_points = 0,
                                knockout_points = 0
                            WHERE group_id = %s AND user_id = %s
                        """
                        execute_query(query,(group_id,user_id))

                        try:
                            await context.bot.send_message(
                                chat_id=group_id,
                                text=f"🎊 {first_name}, congratulations!\n\n"
                                f"You completed your 7-day wellness cycle with {current_points} points! 🏆\n\n"
                                f"🔄 Starting a fresh Day 1 cycle.\n"
                                f"Your points have been reset. Let's go again! 💪",
                            )
                            logger.info(
                                f"Reset 7-day cycle for user {user_id} in group {group_id}"
                            )
                        except Exception as e:
                            logger.error(f"Error sending cycle reset message: {e}")

                    else:
                        # Just advance the day
                        query = "UPDATE group_members SET user_day_number = %s WHERE group_id = %s AND user_id = %s"
                        execute_query(query,(new_day, group_id, user_id))

                        logger.info(
                            f"Advanced user {user_id} in group {group_id} to Day {new_day}"
                        )

    except Exception as e:
        logger.error(f"Error in check_user_day_cycles: {e}")


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
            if not event:
                continue

            event_id = event["event_id"]

            # Get leaderboard
            top_members = db.get_leaderboard(group_id, 10)

            if top_members:
                message = "🏆 **Leaderboard - Top 10**\n\n"

                for i, member in enumerate(top_members, 1):
                    name = member.get("first_name", member.get("username", "Unknown"))
                    earned = member.get("current_points", 0)
                    knockout = member.get("knockout_points", 0)
                    total = earned - knockout

                    medal = ""
                    if i == 1:
                        medal = "🥇"
                    elif i == 2:
                        medal = "🥈"
                    elif i == 3:
                        medal = "🥉"

                    message += f"{medal} {i}. {name} :\n{total} points"
                    if knockout > 0:
                        message += f" ({earned} earned - {knockout} lost)"
                    message += "\n"

                message += "\n📅 Great job everyone! See you tomorrow! 🌟"

                await context.bot.send_message(chat_id=group_id, text=message)
                logger.info(f"Posted daily leaderboard for group {group_id}")

    except Exception as e:
        logger.error(f"Error in post_daily_leaderboard: {e}")


def setup_jobs(application):
    """Setup periodic jobs."""
    job_queue = application.job_queue
    ist=timezone("Asia/Kolkata")

    # Check and announce slots every minute
    job_queue.run_repeating(check_and_announce_slots, interval=60, first=0)

    # Check mid-slot warnings every minute
    job_queue.run_repeating(check_mid_slot_warnings, interval=60, first=30)

    # Check inactive users once daily at 22:00 (10 PM)
    job_queue.run_daily(check_inactive_users, time=time(hour=22, minute=0),tzinfo=ist)

    # Check user day cycles daily at 23:15 (just before first slot)
    job_queue.run_daily(check_user_day_cycles, time=time(hour=9, minute=30),tzinfo=ist)

    # Check low-point users daily at END OF DAY (23:00 - 11 PM)
    job_queue.run_daily(check_low_points, time=time(hour=23, minute=0),tzinfo=ist)

    # Post daily leaderboard at 22:00 (10:00 PM)
    job_queue.run_daily(post_daily_leaderboard, time=time(hour=11, minute=58),tzinfo=ist)

    logger.info("Scheduled jobs setup completed")
