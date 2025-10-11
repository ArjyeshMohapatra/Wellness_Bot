from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
import os
import sys
from datetime import time as dt_time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import database_service as db
import config

logger = logging.getLogger(__name__)

# Track active slots to avoid duplicate announcements
active_slot_announcements = {}

async def check_and_announce_slots(context: ContextTypes.DEFAULT_TYPE):
    """Check for active slots and announce them."""
    try:
        # Get all group configs
        query = "SELECT group_id FROM groups_config"
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            groups = cursor.fetchall()
            cursor.close()
        
        for group in groups:
            group_id = group['group_id']
            
            # Get active slot
            active_slot = db.get_active_slot(group_id)
            
            if active_slot:
                slot_id = active_slot['slot_id']
                slot_name = active_slot['slot_name']
                slot_type = active_slot['slot_type']
                start_time = active_slot['start_time']
                end_time = active_slot['end_time']
                
                if active_slot_announcements.get(group_id) != slot_id:
                    # Format time strings
                    from datetime import datetime
                    
                    if hasattr(start_time, 'total_seconds'):
                        start_str = (datetime.min + start_time).strftime("%H:%M")
                    else:
                        start_str = start_time.strftime("%H:%M") if hasattr(start_time, 'strftime') else str(start_time)
                    
                    if hasattr(end_time, 'total_seconds'):
                        end_str = (datetime.min + end_time).strftime("%H:%M")
                    else:
                        end_str = end_time.strftime("%H:%M") if hasattr(end_time, 'strftime') else str(end_time)
                    
                    # Build message with time
                    message = f"⏰ {slot_name} - Time: {start_str} to {end_str}\n\n"
                    message += active_slot.get('initial_message', f"{slot_name} has started!")
                    
                    # Check for active event to include in announcement
                    active_event = db.get_active_event(group_id)
                    if active_event:
                        message += f"\n📅 Event: {active_event['event_name']}"
                    
                    # For water slots with buttons
                    if slot_type == 'button':
                        keyboard = [
                            [
                                InlineKeyboardButton("1L 💧", callback_data=f"water_1_{slot_id}"),
                                InlineKeyboardButton("2L 💧💧", callback_data=f"water_2_{slot_id}"),
                                InlineKeyboardButton("3L 💧💧💧", callback_data=f"water_3_{slot_id}")
                            ],
                            [
                                InlineKeyboardButton("4L 💧💧💧💧", callback_data=f"water_4_{slot_id}"),
                                InlineKeyboardButton("5L 💧💧💧💧💧", callback_data=f"water_5_{slot_id}")
                            ]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        slot_msg = await context.bot.send_message(
                            chat_id=group_id,
                            text=message,
                            reply_markup=reply_markup
                        )
                    else:
                        image_path = active_slot.get('image_file_path')
                        
                        if image_path and os.path.exists(image_path):
                            with open(image_path, 'rb') as photo:
                                slot_msg = await context.bot.send_photo(
                                    chat_id=group_id,
                                    photo=photo,
                                    caption=message
                                )
                        else:
                            slot_msg = await context.bot.send_message(
                                chat_id=group_id,
                                text=message
                            )
                    
                    # Pin the slot announcement
                    try:
                        await context.bot.pin_chat_message(group_id, slot_msg.message_id)
                    except Exception as pin_error:
                        logger.warning(f"Could not pin slot announcement: {pin_error}")
                    
                    active_slot_announcements[group_id] = slot_id
                    logger.info(f"Announced and pinned slot {slot_name} in group {group_id}")
            
            else:
                # No active slot
                if group_id in active_slot_announcements:
                    del active_slot_announcements[group_id]
    
    except Exception as e:
        logger.error(f"Error in check_and_announce_slots: {e}")

async def check_inactive_users(context: ContextTypes.DEFAULT_TYPE):
    """Check for inactive users: warn at 2 days, kick temporarily at 3 days."""
    try:
        logger.info("Checking for inactive users...")
        from datetime import datetime, timedelta
        
        # Get all groups
        query = "SELECT group_id FROM groups_config"
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            groups = cursor.fetchall()
            cursor.close()
        
        for group in groups:
            group_id = group['group_id']
            
            # Check for 2-day inactive (warning)
            inactive_2day = db.get_inactive_members(group_id, 2)
            
            for member in inactive_2day:
                user_id = member['user_id']
                first_name = member.get('first_name', 'User')
                
                # Check if already warned today
                check_query = """
                    SELECT * FROM inactivity_warnings 
                    WHERE group_id = %s AND user_id = %s AND warning_date = CURDATE() AND warning_type = '2day'
                """
                with get_db_connection() as conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(check_query, (group_id, user_id))
                    existing = cursor.fetchone()
                    cursor.close()
                
                if not existing:
                    try:
                        # Send warning
                        await context.bot.send_message(
                            chat_id=group_id,
                            text=f"⚠️ {first_name}, you've been inactive for 2 days!\n"
                                 f"Please participate in today's activities or you'll be removed tomorrow."
                        )
                        
                        # Log warning
                        insert_query = """
                            INSERT INTO inactivity_warnings (group_id, user_id, warning_date, warning_type)
                            VALUES (%s, %s, CURDATE(), '2day')
                        """
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(insert_query, (group_id, user_id))
                            cursor.close()
                            conn.commit()
                        
                        logger.info(f"Warned 2-day inactive user {user_id} in group {group_id}")
                    
                    except Exception as e:
                        logger.error(f"Error warning user {user_id}: {e}")
            
            # Check for 3-day inactive (kick temporarily)
            inactive_3day = db.get_inactive_members(group_id, 3)
            
            for member in inactive_3day:
                user_id = member['user_id']
                first_name = member.get('first_name', 'User')
                
                try:
                    # Deduct 20 knockout points for 3-day inactivity before kicking
                    db.deduct_knockout_points(group_id, user_id, 20)
                    
                    # Kick temporarily for a few hours (6 hours)
                    until_date = datetime.now() + timedelta(hours=6)
                    await context.bot.ban_chat_member(group_id, user_id, until_date=until_date)
                    
                    # Remove from database
                    db.remove_member(group_id, user_id, 'kicked')
                    
                    # Send notification
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=f"🚫 {first_name} has been temporarily removed due to 3 days of inactivity.\n"
                             f"⚠️ 20 knockout points were deducted.\n"
                             f"They can be re-added by an admin after discussing with them."
                    )
                    
                    logger.info(f"Kicked 3-day inactive user {user_id} from group {group_id}")
                
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
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            events = cursor.fetchall()
            cursor.close()
        
        for event in events:
            group_id = event['group_id']
            min_points = event['min_pass_points']
            
            if min_points <= 0:
                continue
            
            # Get members below minimum
            low_point_members = db.get_low_point_members(group_id, min_points)
            
            for member in low_point_members:
                user_id = member['user_id']
                first_name = member.get('first_name', 'User')
                current_points = member['current_points']
                
                try:
                    from datetime import datetime, timedelta
                    
                    # Kick the user temporarily (1 day)
                    until_date = datetime.now() + timedelta(days=1)
                    await context.bot.ban_chat_member(group_id, user_id, until_date=until_date)
                    
                    # Remove from database
                    db.remove_member(group_id, user_id, 'kicked')
                    
                    # Send congratulations and notification
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=f"� {first_name}, thank you for your participation!\n"
                             f"🎯 You earned {current_points} points - great effort!\n\n"
                             f"Unfortunately, you didn't reach the minimum {min_points} points required.\n"
                             f"💪 Keep trying! You're temporarily removed for 1 day.\n"
                             f"You can rejoin and try again!"
                    )
                    
                    logger.info(f"Kicked low-point user {user_id} from group {group_id}")
                
                except Exception as e:
                    logger.error(f"Error kicking user {user_id}: {e}")
    
    except Exception as e:
        logger.error(f"Error in check_low_points: {e}")

# Track mid-slot warnings already sent
mid_slot_warnings_sent = {}

async def check_mid_slot_warnings(context: ContextTypes.DEFAULT_TYPE):
    """Post warning messages at 50% of slot duration."""
    try:
        from datetime import datetime, time
        
        # Get all groups
        query = "SELECT group_id FROM groups_config"
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            groups = cursor.fetchall()
            cursor.close()
        
        for group in groups:
            group_id = group['group_id']
            
            # Get active slot
            active_slot = db.get_active_slot(group_id)
            
            if active_slot:
                slot_id = active_slot['slot_id']
                slot_name = active_slot['slot_name']
                start_time = active_slot['start_time']
                end_time = active_slot['end_time']
                
                # Convert timedelta to datetime.time if needed
                if hasattr(start_time, 'total_seconds'):
                    start_time = (datetime.min + start_time).time()
                if hasattr(end_time, 'total_seconds'):
                    end_time = (datetime.min + end_time).time()
                
                # Calculate slot duration and mid-point
                now = datetime.now().time()
                
                # Convert times to minutes for comparison
                start_minutes = start_time.hour * 60 + start_time.minute
                end_minutes = end_time.hour * 60 + end_time.minute
                now_minutes = now.hour * 60 + now.minute
                
                # Handle overnight slots
                if end_minutes < start_minutes:
                    end_minutes += 24 * 60
                    if now_minutes < start_minutes:
                        now_minutes += 24 * 60
                
                duration_minutes = end_minutes - start_minutes
                mid_point_minutes = start_minutes + (duration_minutes // 2)
                
                # Check if we're at mid-point (within 1 minute tolerance)
                if abs(now_minutes - mid_point_minutes) <= 1:
                    # Check if warning already sent for this slot today
                    today_key = f"{group_id}_{slot_id}_{datetime.now().date()}"
                    
                    if today_key not in mid_slot_warnings_sent:
                        remaining_minutes = duration_minutes // 2
                        
                        await context.bot.send_message(
                            chat_id=group_id,
                            text=f"⏰ *{slot_name}* - Reminder!\n\n"
                                 f"⚠️ Only {remaining_minutes} minutes remaining!\n"
                                 f"📸 If you haven't posted yet, do it now!",
                            parse_mode='Markdown'
                        )
                        
                        mid_slot_warnings_sent[today_key] = True
                        logger.info(f"Sent mid-slot warning for {slot_name} in group {group_id}")
            
            else:
                # Clear warnings if no active slot
                keys_to_remove = [k for k in mid_slot_warnings_sent.keys() if k.startswith(f"{group_id}_")]
                for key in keys_to_remove:
                    del mid_slot_warnings_sent[key]
    
    except Exception as e:
        logger.error(f"Error in check_mid_slot_warnings: {e}")

async def check_user_day_cycles(context: ContextTypes.DEFAULT_TYPE):
    """Check and update user day cycles, lift restrictions, reset after Day 7."""
    try:
        from datetime import datetime, timedelta
        
        logger.info("Checking user day cycles...")
        
        # Get all groups
        query = "SELECT group_id FROM groups_config"
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            groups = cursor.fetchall()
            cursor.close()
        
        for group in groups:
            group_id = group['group_id']
            
            # Get all members in this group
            query = """
                SELECT user_id, username, first_name, user_day_number, cycle_start_date, 
                       is_restricted, current_points
                FROM group_members
                WHERE group_id = %s
            """
            with get_db_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, (group_id,))
                members = cursor.fetchall()
                cursor.close()
            
            for member in members:
                user_id = member['user_id']
                first_name = member.get('first_name', 'User')
                day_number = member['user_day_number']
                cycle_start = member['cycle_start_date']
                is_restricted = member['is_restricted']
                current_points = member['current_points']
                
                if not cycle_start:
                    continue
                
                # Calculate days since cycle start
                today = datetime.now().date()
                days_elapsed = (today - cycle_start).days
                
                # Lift restriction if user was restricted and it's a new day
                if is_restricted and days_elapsed >= 1:
                    query = "UPDATE group_members SET is_restricted = 0 WHERE group_id = %s AND user_id = %s"
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(query, (group_id, user_id))
                        cursor.close()
                        conn.commit()
                    
                    try:
                        await context.bot.send_message(
                            chat_id=group_id,
                            text=f"🎉 {first_name}, your restriction has been lifted!\n"
                                 f"Welcome to Day 1! You can now participate in activities. 💪"
                        )
                        logger.info(f"Lifted restriction for user {user_id} in group {group_id}")
                    except Exception as e:
                        logger.error(f"Error sending restriction lift message: {e}")
                
                # Update day number if it's a new day (for non-restricted users)
                if not is_restricted and days_elapsed > 0:
                    new_day = days_elapsed + 1
                    
                    # Only update if day actually changed
                    if new_day == day_number:
                        continue  # Day already correct, skip
                    
                    # Check if completed 7 days - reset cycle
                    if new_day > 7:
                        query = """
                            UPDATE group_members 
                            SET user_day_number = 1, 
                                cycle_start_date = CURDATE(),
                                current_points = 0,
                                knockout_points = 0
                            WHERE group_id = %s AND user_id = %s
                        """
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(query, (group_id, user_id))
                            cursor.close()
                            conn.commit()
                        
                        try:
                            await context.bot.send_message(
                                chat_id=group_id,
                                text=f"🎊 {first_name}, congratulations!\n\n"
                                     f"You completed your 7-day wellness cycle with {current_points} points! 🏆\n\n"
                                     f"🔄 Starting a fresh Day 1 cycle.\n"
                                     f"Your points have been reset. Let's go again! 💪"
                            )
                            logger.info(f"Reset 7-day cycle for user {user_id} in group {group_id}")
                        except Exception as e:
                            logger.error(f"Error sending cycle reset message: {e}")
                    
                    else:
                        # Just advance the day
                        query = "UPDATE group_members SET user_day_number = %s WHERE group_id = %s AND user_id = %s"
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(query, (new_day, group_id, user_id))
                            cursor.close()
                            conn.commit()
                        
                        logger.info(f"Advanced user {user_id} in group {group_id} to Day {new_day}")
    
    except Exception as e:
        logger.error(f"Error in check_user_day_cycles: {e}")

async def post_daily_leaderboard(context: ContextTypes.DEFAULT_TYPE):
    """Post leaderboard automatically at end of day (10 PM)."""
    try:
        # Get all group configs
        query = "SELECT group_id FROM groups_config"
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            groups = cursor.fetchall()
            cursor.close()
        
        for group in groups:
            group_id = group['group_id']
            
            # Get active event
            event = db.get_active_event(group_id)
            if not event:
                continue
            
            event_id = event['event_id']
            
            # Get leaderboard
            top_members = db.get_leaderboard(group_id, 10)
            
            if top_members:
                message = "🏆 **End of Day Leaderboard - Top 10**\n\n"
                
                for i, member in enumerate(top_members, 1):
                    name = member.get('first_name', member.get('username', 'Unknown'))
                    earned = member.get('current_points', 0)
                    knockout = member.get('knockout_points', 0)
                    total = earned - knockout
                    
                    medal = ""
                    if i == 1:
                        medal = "🥇"
                    elif i == 2:
                        medal = "🥈"
                    elif i == 3:
                        medal = "🥉"
                    
                    message += f"{medal} {i}. {name}: {total} pts"
                    if knockout > 0:
                        message += f" ({earned} earned - {knockout} lost)"
                    message += "\n"
                
                message += "\n📅 Great job everyone! See you tomorrow! 🌟"
                
                await context.bot.send_message(
                    chat_id=group_id,
                    text=message
                )
                logger.info(f"Posted daily leaderboard for group {group_id}")
    
    except Exception as e:
        logger.error(f"Error in post_daily_leaderboard: {e}")

# Import get_db_connection
from db import get_db_connection

def setup_jobs(application):
    """Setup periodic jobs."""
    job_queue = application.job_queue
    
    # Check and announce slots every minute
    job_queue.run_repeating(check_and_announce_slots, interval=60, first=0)
    
    # Check mid-slot warnings every minute
    job_queue.run_repeating(check_mid_slot_warnings, interval=60, first=30)
    
    # Check inactive users every hour
    job_queue.run_repeating(check_inactive_users, interval=3600, first=300)
    
    # Check low-point users every 6 hours
    job_queue.run_repeating(check_low_points, interval=21600, first=600)
    
    # Check user day cycles daily at 04:00 AM (when first slot starts)
    from datetime import time
    job_queue.run_daily(check_user_day_cycles, time=time(hour=4, minute=0))
    
    # Post daily leaderboard at 10:00 PM (end of day)
    job_queue.run_daily(post_daily_leaderboard, time=time(hour=22, minute=15))
    
    logger.info("Scheduled jobs setup completed")
