import logging
from datetime import datetime, timedelta
from pytz import timezone
from config import NEW_MEMBER_RESTRICTION_MINUTES
from db import execute_query, get_db_connection
import mysql.connector
import json
import base64
import os
from pathlib import Path

ist=timezone("Asia/Kolkata")
logger = logging.getLogger(__name__)


def save_base64_image(base64_data, admin_user_id, slot_name):
    """Save a Base64 encoded image and return the file path."""
    try:
        if not base64_data or not base64_data.startswith('data:image/'):
            return base64_data  # Return as-is if not Base64
        
        # Extract the Base64 data (remove the data:image/... prefix)
        header, encoded = base64_data.split(',', 1)
        image_data = base64.b64decode(encoded)
        
        # Determine file extension from header
        if 'jpeg' in header or 'jpg' in header:
            ext = 'jpg'
        elif 'png' in header:
            ext = 'png'
        elif 'gif' in header:
            ext = 'gif'
        elif 'webp' in header:
            ext = 'webp'
        else:
            ext = 'jpg'  # Default
        
        # Create directory structure
        storage_path = Path('storage/admin_images')
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"admin_{admin_user_id}_{slot_name}_{timestamp}.{ext}"
        file_path = storage_path / filename
        
        # Save the image
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        # Return relative path for storage
        return str(file_path)
        
    except Exception as e:
        logger.error(f"Error saving Base64 image: {e}")
        return base64_data  # Return original data on error


def get_group_config(group_id):
    query = "SELECT * FROM groups_config WHERE group_id = %s"
    result = execute_query(query, (group_id,), fetch=True)
    return result[0] if result else None


# fetches very first slot's starting time
def get_first_slot_time(group_id):
    """Get the start time of the first slot of the day."""
    query = "SELECT start_time FROM group_slots WHERE group_id = %s ORDER BY start_time ASC LIMIT 1"
    result = execute_query(query, (group_id,), fetch=True)
    return result[0]["start_time"] if result else None


# REPLACE the old function with this one
def get_restriction_until_time(group_id):
    """
    Calculates the restriction time for a new member using NAIVE datetime objects in IST.
    """
    now_ist = datetime.now(ist)
    first_slot_timedelta = get_first_slot_time(group_id)

    if not first_slot_timedelta:
        # Fallback if no slots are defined: restrict for a few minutes.
        return (now_ist + timedelta(minutes=NEW_MEMBER_RESTRICTION_MINUTES)).replace(
            tzinfo=None
        )

    first_slot_time = (datetime.min + first_slot_timedelta).time()

    # Get the time of the first slot on today's date
    first_slot_today_ist = ist.localize(
        datetime.combine(now_ist.date(), first_slot_time)
    )

    if now_ist < first_slot_today_ist:
        # If the user joins BEFORE the first slot today, restrict them until that slot starts.
        return first_slot_today_ist.replace(tzinfo=None)
    else:
        # If the user joins AFTER the first slot today, restrict them until the first slot TOMORROW.
        tomorrow_date = (now_ist + timedelta(days=1)).date()
        first_slot_tomorrow_ist = ist.localize(
            datetime.combine(tomorrow_date, first_slot_time)
        )
        return first_slot_tomorrow_ist.replace(tzinfo=None)


def create_group_config(group_id, admin_user_id):
    try:
        # Check if group config already exists
        existing_config = get_group_config(group_id)

        if not existing_config:
            license_key = f"AUTO_{group_id}_{int(datetime.now(ist).timestamp())}"

            execute_query(
                "INSERT INTO licenses (license_key, is_active, assigned_group_id, assigned_admin_id) VALUES (%s, TRUE, %s, %s)",
                (license_key, group_id, admin_user_id),
            )

            execute_query(
                """
                    INSERT INTO groups_config 
                    (group_id, license_key, admin_user_id, max_members, welcome_message, kick_message)
                    VALUES (%s, %s, %s, 100, 'Welcome! Hoping that you will enjoy your time in here. 🌟', 'Goodbye, hope you enjoyed your time while being with us!')
                """,
                (group_id, license_key, admin_user_id),
            )

            logger.info(f"Created group config for {group_id}")

        # Always try to create event and slots (will check if they exist)
        create_default_event_and_slots(group_id)

        return True
    except Exception as e:
        logger.error(f"Error creating group config: {e}",exc_info=True)
        return False


def create_default_event_and_slots(group_id):
    try:
        # Check if slots already exist for this group
        existing_slots = get_all_slots(group_id)
        if existing_slots:
            logger.info(f"Slots already exist for group {group_id}, skipping creation")
            return True

        # Create a 7-day ongoing wellness event
        start_date = datetime.now(ist).date()
        end_date = start_date + timedelta(days=7)

        query = """
                INSERT INTO events 
                (group_id, event_name, start_date, end_date, min_pass_points, is_active)
                VALUES (%s, 'Wellness Challenge', %s, %s, 250, TRUE)
            """
        event_id = execute_query(query, (group_id, start_date, end_date))

        logger.info(f"Created wellness event {event_id} for group {group_id}")

        slots = [
            (
                "Good Morning",
                "10:40:00",
                "10:45:00",
                "media",
                10,
                "Its Good morning everyone! Share your morning photo 🌅",
                "Great start to your day! ✅",
                "Is this your Good Morning ?",
            ),
            (
                "Workout",
                "10:50:00",
                "10:55:00",
                "media",
                10,
                "Its Workout time everyone! Post your exercise photo 💪",
                "Amazing workout! 💪",
                "Is this your Workout ?",
            ),
            (
                "Breakfast",
                "11:00:00",
                "11:05:00",
                "media",
                10,
                "Its Breakfast time everyone! Share your delicious & healthy meal 🍳",
                "Healthy breakfast! 🍳",
                "Is this your Breakfast ?",
            ),
            (
                "Water",
                "11:10:00",
                "11:15:00",
                "button",
                10,
                "Lets checkout your morning hydration everyone! How much water did everyone drink ? 💧",
                "Great hydration! 💧",
                "Is this the amount of water you drank ?",
            ),
            (
                "Lunch",
                "11:20:00",
                "11:25:00",
                "media",
                10,
                "Its Lunch time everyone! Post your delicious meal 🍱",
                "Nutritious lunch! 🍱",
                "Is this your lunch ?",
            ),
            (
                "Water",
                "11:30:00",
                "11:35:00",
                "button",
                10,
                "Lets checkout your afternoon hydration everyone! How much water did everyone drink ? 💧",
                "Great hydration! 💧",
                "Is this the amount of water you drank ?",
            ),
            (
                "Snacks",
                "11:40:00",
                "11:45:00",
                "media",
                10,
                "Evening snack time! Share your healthy snack 🍎",
                "Healthy snack! 🍎",
                "Is this your evening snacks ?",
            ),
            (
                "Water",
                "11:50:00",
                "11:55:00",
                "button",
                10,
                "Lets checkout how hydrated are you in evening! Track your water 💧",
                "Great hydration! 💧",
                "Is this the amount of water you drank ?",
            ),
            (
                "Dinner",
                "12:00:00",
                "12:05:00",
                "media",
                10,
                "Its Dinner time everyone! Share your healthy meal 🍽️",
                "Delicious dinner! 🍽️",
                "Is this your dinner ?",
            ),
        ]

        slot_keywords = {
            "Good Morning": ["good morning", "morning"],
            "Workout": ["workout", "running"],
            "Breakfast": ["breakfast", "morning meal"],
            "Water Intake": ["100ml", "200ml", "300ml", "400ml", "500ml", "600ml", "700ml", "800ml", "900ml", "1l", "2l", "3l", "4l", "5l"],
            "Lunch": ["lunch", "afternoon meal"],
            "Water Intake": ["100ml", "200ml", "300ml", "400ml", "500ml", "600ml", "700ml", "800ml", "900ml", "1l", "2l", "3l", "4l", "5l"],
            "Evening Snacks": ["snacks", "evening snack"],
            "Water Intake": ["100ml", "200ml", "300ml", "400ml", "500ml", "600ml", "700ml", "800ml", "900ml", "1l", "2l", "3l", "4l", "5l"],
            "Dinner": ["dinner", "night meal"],
        }

        for (slot_name, start_time, end_time, slot_type, slot_points, initial_msg, response_pos, response_clar) in slots:
            is_mandatory = 0 if slot_name == "Evening Snacks" else 1

            query = """
                    INSERT INTO group_slots 
                    (group_id, event_id, slot_name, start_time, end_time, 
                        initial_message, response_positive, response_clarify, image_file_path, slot_type, slot_points, is_mandatory)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            slot_id = execute_query(
                query, (group_id, event_id, slot_name, start_time, end_time, initial_msg, response_pos, response_clar, None, slot_type, slot_points, is_mandatory)
                )

            # Add keywords for this slot
            if slot_name in slot_keywords:
                for keyword in slot_keywords[slot_name]:
                    query = """
                    INSERT INTO slot_keywords (slot_id, keyword) VALUES (%s, %s)
                    """
                    execute_query(query, (slot_id, keyword))
        logger.info(
            f"Created {len(slots)} default slots with multilingual keywords for group {group_id}"
        )
        return True

    except Exception as e:
        logger.error(f"Error creating default slots: {e}",exc_info=True)
        return False

# gets info regarding members who joins back group
def get_returning_member_info(group_id, user_id):
    """
    Checks if a user is in the history.
    Returns their most recent record (as a dict) if found, otherwise None.
    """
    # gets most recent history about an user
    query="""
    SELECT * FROM member_history WHERE group_id = %s AND user_id = %s ORDER BY action_at DESC LIMIT 1
    """
    result = execute_query(query, (group_id, user_id), fetch=True)
    return result[0] if result else None # Returns all columns or None

def add_member(group_id, user_id, username=None, first_name=None, last_name=None, is_admin=False, restrict_new=True):
    """
    Atomically adds or updates a member using INSERT ... ON DUPLICATE KEY UPDATE.
    Returns the member's data and a boolean indicating if they were newly inserted.
    """
    try:
        # checks if the member exists to determine if this is a new join
        existing = get_member(group_id, user_id)
        is_new = existing is None

        is_restricted = 0
        restriction_until = None
        
        # Default values for a truly new member
        cycle_start_date = None
        cycle_end_date = None
        total_points = 0
        knockout_points = 0
        general_warnings = 0
        banned_word_count = 0
        user_day_number = 1

        if is_new:
            # Check if this "new" member is actually a returning member
            last_record = get_returning_member_info(group_id, user_id)

            apply_restriction = False

            if is_admin:
                # Admins are never restricted
                apply_restriction = False
                logger.info(f"💼 DB: New admin {user_id} joined. No restriction.")

            elif last_record is None:
                # Truly new member
                apply_restriction = restrict_new
                logger.info(f"🔒 DB: New member {user_id}. Applying restriction." if restrict_new else f"👋 DB: Existing member {user_id} added without restriction.")

            elif last_record['action'] in ['kicked', 'banned']:
                # Kicked or banned members are ALWAYS re-restricted
                apply_restriction = True
                logger.info(f"🔒 DB: Returning member {user_id} (was {last_record['action']}). Applying restriction.")

            elif last_record['action'] == 'left':
                # User left voluntarily. Restore their stats
                # Checks if user was restricted before leaving or not
                if last_record['is_restricted'] == 1:
                    apply_restriction = True
                    logger.info(f"🔒 DB: Returning member {user_id} (left while restricted). Applying restriction.")
                else:
                    apply_restriction = False
                    logger.info(f"👋 DB: Returning member {user_id} (left while active). Restoring stats. No restriction.")
                
                # Restore their old stats regardless of their restriction
                total_points = last_record.get('total_points', 0)
                knockout_points = last_record.get('knockout_points', 0)
                general_warnings = last_record.get('general_warnings', 0)
                banned_word_count = last_record.get('banned_word_count', 0)
                user_day_number = last_record.get('user_day_number', 1)
                cycle_start_date = last_record.get('cycle_start_date')
                cycle_end_date = last_record.get('cycle_end_date')
                
                # if cycle dates are missing or are expired then reset them
                if not cycle_start_date or (cycle_end_date and datetime.now(ist).date() > cycle_end_date):
                    cycle_start_date = datetime.now(ist).date()
                    cycle_end_date = cycle_start_date + timedelta(days=7)
                    user_day_number = 1 # resets day number for user to 1 if reset happens
            else:
                # Fallback case
                apply_restriction = False
                logger.info(f"👋 DB: Returning member {user_id} (left while active). No restriction.")

            if apply_restriction:
                is_restricted = 1
                restriction_until = get_restriction_until_time(group_id)
                if restriction_until is not None:
                    restriction_until = restriction_until.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Restriction for {user_id} will be until {restriction_until} (IST).")
            else:
                # Not restricted, set cycle dates
               if not cycle_start_date:
                    cycle_start_date = datetime.now(ist).date()
                    cycle_end_date = cycle_start_date + timedelta(days=7)
                    
        query_1 = """
            INSERT INTO group_members (
                user_id, group_id, username, first_name, last_name, is_admin, 
                is_restricted, restriction_until, cycle_start_date, cycle_end_date, 
                total_points, knockout_points, general_warnings, banned_word_count, user_day_number,
                joined_at, last_active_timestamp
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                first_name = VALUES(first_name),
                last_name = VALUES(last_name),
                is_admin = VALUES(is_admin),
                last_active_timestamp = NOW()
        """
        
        query_2 = """
                INSERT INTO member_history (
                    group_id, user_id, username, first_name, last_name, 
                    total_points, knockout_points, general_warnings, banned_word_count,
                    user_day_number, cycle_start_date, cycle_end_date, joined_at,
                    last_active_timestamp, action
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), 'joined')
            """
                   
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # handles both INSERT for new members and UPDATE for existing ones
                cursor.execute(query_1, (
                    user_id, group_id, username, first_name, last_name, 1 if is_admin else 0, 
                    is_restricted, restriction_until, cycle_start_date, cycle_end_date,
                    total_points, knockout_points, general_warnings, banned_word_count, user_day_number
                ))
                
                # If member is new, also log to member_history table
                if is_new:
                    cursor.execute(query_2, (
                        group_id, user_id, username, first_name, last_name, 
                        total_points, knockout_points, general_warnings, banned_word_count,
                        user_day_number, cycle_start_date, cycle_end_date
                    ))
                    logger.debug(f"[DEBUG] Complete 'joined' record created for new user {user_id}")
        member_data = get_member(group_id, user_id)
        return member_data, is_new

    except mysql.connector.Error as e:
        logger.error("DATABASE ERROR during transaction in add_member for user %s: %s",user_id, e,exc_info=True)
        return None, False

    except Exception as e:
        logger.error("UNEXPECTED ERROR in add_member for user %s: %s",user_id, e,exc_info=True)
        return None, False


def update_member_activity(group_id, user_id):
    query = "UPDATE group_members SET last_active_timestamp = NOW() WHERE group_id = %s AND user_id = %s"
    execute_query(query, (group_id, user_id))


def get_member(group_id, user_id):
    query = "SELECT * FROM group_members WHERE group_id = %s AND user_id = %s"
    result = execute_query(query, (group_id, user_id), fetch=True)
    return result[0] if result else None


# updates banned word counts per user
def add_banned_words_warning(group_id, user_id):
    query = "UPDATE group_members SET banned_word_count = banned_word_count + 1 WHERE group_id = %s AND user_id = %s"
    execute_query(query, (group_id, user_id))


# updates general warning count per user
def add_general_warning(group_id, user_id):
    query = "UPDATE group_members SET general_warnings = general_warnings + 1 WHERE group_id = %s AND user_id = %s"
    execute_query(query, (group_id, user_id))


def deduct_knockout_points(group_id, user_id, points):
    """Deduct knockout points and subtract from current points."""
    try:
        query = """
                UPDATE group_members 
                SET knockout_points = knockout_points + %s,
                    total_points = GREATEST(0, total_points - %s)
                WHERE group_id = %s AND user_id = %s
            """
        execute_query(query, (points, points, group_id, user_id))
        logger.info(
            f"Deducted {points} knockout points from user {user_id} in group {group_id}"
        )
        return True
    except Exception as e:
        logger.error(f"Error deducting knockout points: {e}",exc_info=True)
        return False


def get_inactive_members(group_id, days=3):
    query = """
            SELECT user_id, username, first_name, last_active_timestamp
            FROM group_members
            WHERE group_id = %s 
            AND last_active_timestamp < DATE_SUB(NOW(), INTERVAL %s DAY)
        """
    return execute_query(query, (group_id, days), fetch=True)


def log_inactivity_warning(group_id, user_id, warning_type, member_details):
    query = """
        INSERT INTO inactivity_warnings (group_id, user_id, username, first_name, last_name, warning_date, warning_type)
        VALUES (%s, %s, %s, %s, %s, CURDATE(), %s)
    """
    execute_query(
        query,
        (
            group_id,
            user_id,
            member_details.get("username"),
            member_details.get("first_name"),
            member_details.get("last_name"),
            warning_type,
        ),
    )

# Stores a complete snapshot of a member to member_history and then deletes them from group_members
def remove_member(group_id, user_id, action="kicked"):
    try:
        member = get_member(group_id, user_id)
        if not member:
            # If member is already gone, just log it as a safety measure.
            execute_query("INSERT INTO member_history (group_id, user_id, action) VALUES (%s, %s, %s)", (group_id, user_id, action))
            return True

        # Archive all relevant data to the history table AND delete in a single transaction
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                archive_query = """
                INSERT INTO member_history (
                    group_id, user_id, username, first_name, last_name,
                    total_points, knockout_points, general_warnings, banned_word_count,
                    user_day_number, cycle_start_date, cycle_end_date, is_restricted, joined_at, 
                    last_active_timestamp, action
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(archive_query, (
                member['group_id'], member['user_id'], member.get('username'), member.get('first_name'), member.get('last_name'),
                member.get('total_points'), member.get('knockout_points'), member.get('general_warnings'), member.get('banned_word_count'),
                member.get('user_day_number'), member.get('cycle_start_date'), member.get('cycle_end_date'), member.get('is_restricted', 0), 
                member.get('joined_at'), member.get('last_active_timestamp'), action
                ))

                # Finally, delete the member from the main table
                cursor.execute("DELETE FROM group_members WHERE group_id = %s AND user_id = %s", (group_id, user_id))
                conn.commit()  # Ensure both operations are committed together
        logger.info(f"Archived and removed member {user_id} from group {group_id}.")
        return True
    except Exception as e:
        logger.error(f"Error removing member {user_id}: {e}", exc_info=True)
        return False


def get_active_event(group_id):
    query = """
            SELECT * FROM events 
            WHERE group_id = %s AND is_active = TRUE
            AND CURDATE() BETWEEN start_date AND end_date
            LIMIT 1
        """
    result = execute_query(query, (group_id,), fetch=True)
    return result[0] if result else None


def get_active_slot(group_id):
    query = """
            SELECT * FROM group_slots
            WHERE group_id = %s
            AND (
                (start_time <= end_time AND CURTIME() BETWEEN start_time AND end_time)
                OR
                (start_time > end_time AND (CURTIME() >= start_time OR CURTIME() <= end_time))
            )
            LIMIT 1
        """
    result = execute_query(query, (group_id,), fetch=True)
    return result[0] if result else None


def get_all_slots(group_id):
    query = "SELECT * FROM group_slots WHERE group_id = %s ORDER BY start_time"
    return execute_query(query, (group_id,), fetch=True)


def get_slot_keywords(slot_id):
    query = "SELECT keyword FROM slot_keywords WHERE slot_id = %s"
    results = execute_query(query, (slot_id,), fetch=True)
    return [r["keyword"] for r in results] if results else []


def log_activity(group_id, user_id, activity_type, slot_name, username=None, first_name=None, last_name=None, message_content=None,
                 telegram_file_id=None, local_file_path=None, points_earned=0, is_valid=True):
    query = """
            INSERT INTO user_activity_log 
            (group_id, user_id, activity_type, slot_name,username, first_name, last_name, message_content, 
             telegram_file_id, local_file_path, points_earned, is_valid)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    execute_query(query, (group_id, user_id, activity_type, slot_name, username, first_name, last_name, message_content, telegram_file_id,
                          local_file_path, points_earned, is_valid))


def add_points(group_id, user_id, points, event_id=None):
    """Adds points to a user's total score."""
    try:
        query = "UPDATE group_members SET total_points = total_points + %s WHERE group_id = %s AND user_id = %s"
        execute_query(query, (points, group_id, user_id))
        return True
    except Exception as e:
        logger.error(f"Error adding points: {e}", exc_info=True)
        return False


def get_low_point_members(group_id, min_points):
    query = """
            SELECT user_id, username, first_name, total_points
            FROM group_members
            WHERE group_id = %s AND total_points < %s
        """
    return execute_query(query, (group_id, min_points), fetch=True)


def mark_slot_completed(group_id, event_id, slot_id, user_id, status="completed", points=0):
    """
    Attempts to mark a slot as completed.
    Returns True if a new row was inserted (first completion).
    Returns False if the row already existed (duplicate submission).
    """
    member = get_member(group_id, user_id)

    if member:
        username = member.get("username")
        first_name = member.get("first_name")
        last_name = member.get("last_name")
    else:
        username, first_name, last_name = None, None, None

    query = """
        INSERT INTO daily_slot_tracker (event_id, slot_id, user_id, username, first_name, last_name, log_date, status, points_scored)
        VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s, %s)
        ON DUPLICATE KEY UPDATE duplicate_submissions = duplicate_submissions + 1
    """

    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, (event_id, slot_id, user_id, username, first_name, last_name, status, points))
            return cursor.rowcount == 1


def check_slot_completed_today(event_id, slot_id, user_id):
    """DEPRECATED: This check is now handled atomically inside mark_slot_completed."""
    query = """
            SELECT COUNT(*) as count FROM daily_slot_tracker
            WHERE event_id = %s AND slot_id = %s AND user_id = %s 
            AND log_date = CURDATE()
        """
    result = execute_query(query, (event_id, slot_id, user_id), fetch=True)
    return result[0]["count"] > 0 if result else False


def get_banned_words(group_id):
    query = "SELECT word FROM banned_words WHERE group_id = %s OR group_id IS NULL"
    results = execute_query(query, (group_id,), fetch=True)
    return [r["word"] for r in results] if results else []


def get_leaderboard(group_id, limit=10):
    """
    Fetches the top members for the leaderboard, only including those
    with a net score greater than 0.
    """
    query = """
            SELECT user_id, username, first_name, total_points, knockout_points, user_day_number,
                   (total_points - knockout_points) AS net_points
            FROM group_members
            WHERE group_id = %s AND (total_points - knockout_points) > 0
            ORDER BY net_points DESC
            LIMIT %s
        """
    return execute_query(query, (group_id, limit), fetch=True)


def penalize_zero_activity_members(group_id, event_id, points_to_deduct):
    """Finds members with no slot completions for today and deducts knockout points."""
    try:
        query_1 = """
            SELECT DISTINCT user_id 
            FROM daily_slot_tracker 
            WHERE event_id = %s AND log_date = CURDATE() AND status = 'completed'
        """
        active_members_result = execute_query(query_1, (event_id,), fetch=True)
        active_user_ids = {row["user_id"] for row in active_members_result}

        # Get all non-restricted members in the group.
        query_2 = """
            SELECT user_id, first_name 
            FROM group_members 
            WHERE group_id = %s AND is_restricted = 0
        """
        all_members = execute_query(query_2, (group_id,), fetch=True)

        inactive_members = []
        for member in all_members:
            if member["user_id"] not in active_user_ids:
                inactive_members.append(member)

        # Apply a penalty to each inactive member.
        for member in inactive_members:
            user_id = member["user_id"]
            first_name = member.get("first_name", f"User_{user_id}")
            deduct_knockout_points(group_id, user_id, points_to_deduct)
            logger.info(
                f"Penalized {first_name} ({user_id}) with {points_to_deduct} knockout points for zero activity today."
            )
        return inactive_members
    except Exception as e:
        logger.error(f"Error in penalize_zero_activity_members: {e}", exc_info=True)
        return []


def set_runtime_state(group_id, key, value):
    """Sets or updates a runtime state variable for a group."""
    query = """
    INSERT INTO runtime_state (group_id,state_key,state_value) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE state_value=VALUES(state_value)
    """
    execute_query(query, (group_id, key, str(value) if value is not None else None))


def get_runtime_state(group_id, key):
    """Gets a runtime state variable for a group."""
    query = """
    SELECT state_value FROM runtime_state WHERE group_id = %s AND state_key = %s
    """
    result = execute_query(query, (group_id, key), fetch=True)
    return result[0]["state_value"] if result else None

def update_admin_status(group_id, admin_user_ids):
    """
    Synchronizes the admin status for all members in a group within a single transaction.
    Sets is_admin = 1 for users in the admin_user_ids list and 0 for all others.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query_1="""
                UPDATE group_members SET is_admin = 0 WHERE group_id = %s
                """
                cursor.execute(query_1,(group_id,))
                
                if admin_user_ids:
                    placeholders = ', '.join(['%s'] * len(admin_user_ids))
                    query_2=f"UPDATE group_members SET is_admin = 1 WHERE group_id = %s AND user_id IN ({placeholders})"
                    params=(group_id,)+tuple(admin_user_ids)
                    cursor.execute(query_2,params)
                conn.commit()
        logger.info(f"Successfully synchronized admin status for group {group_id}.")
        return True
    except Exception as e:
        logger.error(f"Failed to synchronize admin status for group {group_id}: {e}", exc_info=True)
        return False
    
def log_missed_slots(group_id, event_id, slot_id):
    """
    Finds all non-restricted members who did not complete a slot
    and marks it as 'missed' in the daily_slot_tracker.
    """
    try:
        get_query="""
        SELECT user_id, username, first_name, last_name FROM group_members WHERE group_id = %s AND is_restricted = 0
        """
        non_restricted_members=execute_query(get_query, (group_id,), fetch=True)
        if not non_restricted_members:
            return # no active members to log
        completed_query="""
        SELECT DISTINCT user_id FROM daily_slot_tracker WHERE event_id = %s AND slot_id = %s AND log_date = CURDATE()
        """
        completed_result=execute_query(completed_query, (event_id, slot_id), fetch=True)
        completed_user_ids={row['user_id'] for row in completed_result}
        
        missed_members_data = []
        for member in non_restricted_members:
            if member['user_id'] not in completed_user_ids:
                missed_members_data.append((
                    event_id, slot_id, 
                    member['user_id'], 
                    member.get('username'), 
                    member.get('first_name'), 
                    member.get('last_name'), 'missed'
                    ))
        if missed_members_data:
            insert_query="""
            INSERT IGNORE INTO daily_slot_tracker (
                event_id, slot_id, user_id, username, first_name, last_name, 
                log_date, status, points_scored) VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s, 0)
            """
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.executemany(insert_query, missed_members_data)
            
            logger.info(f"Logged {len(missed_members_data)} 'missed' entries for slot {slot_id} in group {group_id}", exc_info=True)
    except Exception as e:
        logger.error(f"Error in log_missed_slots_for_group: {e}", exc_info=True)


# ADMIN PANEL SAVE FUNCTIONS

def save_admin_panel_config(admin_user_id, group_id, config_data):
    """
    Save admin panel configuration data to database.
    This function handles saving group config, events, and slots in a transaction.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Start transaction
                conn.start_transaction()

                # 1. Update group configuration
                update_group_config(cursor, group_id, admin_user_id, config_data)

                # 2. Save/Update event (only if group_id is provided)
                event_id = None
                if group_id is not None:
                    event_id = save_or_update_event(cursor, group_id, config_data)

                # 3. Save/Update slots
                save_or_update_slots(cursor, group_id, admin_user_id, event_id, config_data['slots'])

                # 4. Save/Update banned words
                save_banned_words(cursor, None, config_data.get('banned_words', ''))

                # Commit transaction
                conn.commit()

                logger.info(f"Successfully saved admin panel config for group {group_id} by admin {admin_user_id}")
                return True

    except Exception as e:
        logger.error(f"Error saving admin panel config: {e}", exc_info=True)
        # Rollback will happen automatically if we don't commit
        return False


def save_admin_config(admin_user_id, config_data):
    """
    Save admin configuration data to admin_configs table.
    This saves the configuration template that will be applied to groups later.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Start transaction
                conn.start_transaction()

                # 1. Save/Update admin config
                update_admin_config(cursor, admin_user_id, config_data)

                # 2. Save/Update admin slots
                save_or_update_admin_slots(cursor, admin_user_id, config_data['slots'])

                # 3. Save/Update banned words for admin template
                save_banned_words(cursor, None, config_data.get('banned_words', ''))

                # Commit transaction
                conn.commit()

                logger.info(f"Successfully saved admin config for admin {admin_user_id}")
                return True

    except Exception as e:
        logger.error(f"Error saving admin config: {e}", exc_info=True)
        # Rollback will happen automatically if we don't commit
        return False


def update_admin_config(cursor, admin_user_id, config_data):
    """Update admin configuration in admin_configs table"""
    query = """
        INSERT INTO admin_configs 
        (admin_user_id, event_type, event_name, event_days, pass_points, slots_per_day, welcome_message, kick_response, undesignated_slot_response, leaderboard_time, max_members)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            event_type = VALUES(event_type),
            event_name = VALUES(event_name),
            event_days = VALUES(event_days),
            pass_points = VALUES(pass_points),
            slots_per_day = VALUES(slots_per_day),
            welcome_message = VALUES(welcome_message),
            kick_response = VALUES(kick_response),
            undesignated_slot_response = VALUES(undesignated_slot_response),
            leaderboard_time = VALUES(leaderboard_time),
            max_members = VALUES(max_members)
    """

    params = (
        admin_user_id,
        config_data.get('event_type', 'normal'),
        config_data.get('event_name', 'Wellness Challenge'),
        config_data.get('event_days', 0),
        config_data.get('pass_points', 250),
        config_data.get('slots_per_day', 0),
        config_data.get('welcome_message', ''),
        config_data.get('kick_response', ''),
        config_data.get('undesignated_slot_response', ''),
        config_data.get('leaderboard_time', None),
        config_data.get('max_members', 25)
    )
    cursor.execute(query, params)


def save_or_update_admin_slots(cursor, admin_user_id, slots_data):
    """Save or update admin slots"""
    # First, delete existing slots for this admin
    cursor.execute("DELETE FROM admin_slot_keywords WHERE slot_id IN (SELECT slot_id FROM admin_slots WHERE admin_user_id = %s)", (admin_user_id,))
    cursor.execute("DELETE FROM admin_slots WHERE admin_user_id = %s", (admin_user_id,))

    # Insert new slots
    for slot_data in slots_data:
        query = """
            INSERT INTO admin_slots 
            (admin_user_id, slot_name, start_time, end_time, initial_message, response_positive, response_clarify, image_file_path, slot_type, slot_points, is_mandatory, button_count, button_names, button_values)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            admin_user_id,
            slot_data.get('name', ''),
            slot_data.get('startTime', '00:00'),
            slot_data.get('endTime', '00:00'),
            slot_data.get('botResponse', ''),
            slot_data.get('postResponse', ''),
            '',  # response_clarify
            slot_data.get('image', ''),
            slot_data.get('type', 'media'),
            slot_data.get('points', 0),
            slot_data.get('compulsory', False),
            slot_data.get('buttonCount', 0),
            json.dumps(slot_data.get('buttonNames', [])),
            json.dumps(slot_data.get('buttonValues', []))
        )
        cursor.execute(query, params)


def get_admin_config(admin_user_id):
    """
    Get admin configuration from admin_configs table.
    Returns data in the format expected by the frontend.
    """
    try:
        # Get admin config
        query = "SELECT * FROM admin_configs WHERE admin_user_id = %s"
        result = execute_query(query, (admin_user_id,), fetch=True)
        if not result:
            return None

        admin_config = result[0]

        # Get admin slots
        slots = get_admin_slots(admin_user_id)

        # Format response
        config = {
            'admin_user_id': admin_user_id,
            'welcome_message': admin_config.get('welcome_message', ''),
            'kick_response': admin_config.get('kick_response', ''),
            'undesignated_slot_response': admin_config.get('undesignated_slot_response', ''),
            'leaderboard_time': str(admin_config.get('leaderboard_time', '')) if admin_config.get('leaderboard_time') else '',
            'max_members': admin_config.get('max_members', 25),
            'event_name': admin_config.get('event_name', 'Wellness Challenge'),
            'event_type': admin_config.get('event_type', 'normal'),
            'event_days': admin_config.get('event_days', 0),
            'slots_per_day': admin_config.get('slots_per_day', 0),
            'pass_points': admin_config.get('pass_points', 250),
            'slots': []
        }

        # Format slots
        for slot in slots:
            config['slots'].append({
                'name': slot.get('slot_name', ''),
                'compulsory': slot.get('is_mandatory', False),
                'startTime': str(slot.get('start_time', '')),
                'endTime': str(slot.get('end_time', '')),
                'points': slot.get('slot_points', 0),
                'type': 'button' if slot.get('slot_type') == 'button' else 'media',
                'botResponse': slot.get('initial_message', ''),
                'postResponse': slot.get('response_positive', ''),
                'image': slot.get('image_file_path', ''),
                'buttonCount': slot.get('button_count', 0),
                'buttonNames': json.loads(slot.get('button_names', '[]')),
                'buttonValues': json.loads(slot.get('button_values', '[]'))
            })

        return config

    except Exception as e:
        logger.error(f"Error getting admin config: {e}", exc_info=True)
        return None


def get_admin_slots(admin_user_id):
    """Get all slots for an admin"""
    query = "SELECT * FROM admin_slots WHERE admin_user_id = %s ORDER BY start_time ASC"
    result = execute_query(query, (admin_user_id,), fetch=True)
    return result if result else []


def update_group_config(cursor, group_id, admin_user_id, config_data):
    """Update group configuration in groups_config table"""
    if group_id is None:
        # For admin templates, check if config already exists for this admin
        cursor.execute("SELECT config_id FROM groups_config WHERE group_id IS NULL AND admin_user_id = %s", (admin_user_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing admin template
            query = """
                UPDATE groups_config SET
                    license_key = %s, welcome_message = %s, kick_message = %s, 
                    max_members = %s, undesignated_slot_response = %s, leaderboard_time = %s
                WHERE config_id = %s
            """
            params = (
                None,  # license_key
                config_data.get('welcome_message', ''),
                config_data.get('kick_response', ''),  # kick_response maps to kick_message
                config_data.get('max_members', 100),
                config_data.get('undesignated_slot_response', ''),
                config_data.get('leaderboard_time', None),
                existing[0]  # config_id
            )
        else:
            # Insert new admin template
            query = """
                INSERT INTO groups_config (group_id, license_key, admin_user_id, welcome_message, kick_message, max_members, undesignated_slot_response, leaderboard_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                None,  # group_id
                None,  # license_key
                admin_user_id,
                config_data.get('welcome_message', ''),
                config_data.get('kick_response', ''),  # kick_response maps to kick_message
                config_data.get('max_members', 100),
                config_data.get('undesignated_slot_response', ''),
                config_data.get('leaderboard_time', None)
            )
    else:
        # Update existing config with group_id
        query = """
            INSERT INTO groups_config (group_id, license_key, admin_user_id, welcome_message, kick_message, max_members, undesignated_slot_response, leaderboard_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                license_key = VALUES(license_key),
                welcome_message = VALUES(welcome_message),
                kick_message = VALUES(kick_message),
                max_members = VALUES(max_members),
                undesignated_slot_response = VALUES(undesignated_slot_response),
                leaderboard_time = VALUES(leaderboard_time)
        """
        # For now, license_key can be NULL until it's generated later
        license_key = config_data.get('license_key', None)

        params = (
            group_id,
            license_key,
            admin_user_id,
            config_data.get('welcome_message', ''),
            config_data.get('kick_response', ''),  # kick_response maps to kick_message
            config_data.get('max_members', 100),
            config_data.get('undesignated_slot_response', ''),
            config_data.get('leaderboard_time', None)
        )
    cursor.execute(query, params)


def save_or_update_event(cursor, group_id, config_data):
    """Save or update event configuration"""
    from datetime import datetime, timedelta

    event_name = config_data.get('event_name', 'Wellness Challenge')
    event_type = config_data.get('event_type', 'normal')
    event_days = int(config_data.get('event_days', 0)) if config_data.get('event_days') else 0
    pass_points = int(config_data.get('pass_points', 250)) if config_data.get('pass_points') else 250

    # Calculate start and end dates
    start_date = datetime.now(ist).date()
    if event_type == 'time-limited' and event_days > 0:
        end_date = start_date + timedelta(days=event_days - 1)  # -1 because start day counts
        is_active = True
    else:
        # For normal events, set a far future date
        end_date = start_date + timedelta(days=365*10)  # 10 years
        is_active = True

    # Check if event already exists
    cursor.execute("SELECT event_id FROM events WHERE group_id = %s", (group_id,))
    existing_event = cursor.fetchone()

    if existing_event:
        # Update existing event
        query = """
            UPDATE events
            SET event_name = %s, event_type = %s, event_days = %s, slots_per_day = %s,
                start_date = %s, end_date = %s, min_pass_points = %s, is_active = %s
            WHERE group_id = %s
        """
        params = (event_name, event_type, event_days, config_data.get('slots_per_day', 0),
                 start_date, end_date, pass_points, is_active, group_id)
        cursor.execute(query, params)
        return existing_event[0]
    else:
        # Create new event
        query = """
            INSERT INTO events (group_id, event_name, event_type, event_days, slots_per_day,
                               start_date, end_date, min_pass_points, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (group_id, event_name, event_type, event_days, config_data.get('slots_per_day', 0),
                 start_date, end_date, pass_points, is_active)
        cursor.execute(query, params)
        return cursor.lastrowid


def save_or_update_slots(cursor, group_id, admin_user_id, event_id, slots_data):
    """Save or update slot configurations"""
    # First, get existing slots for this group or admin
    if group_id is not None:
        cursor.execute("SELECT slot_id, slot_name FROM group_slots WHERE group_id = %s", (group_id,))
    else:
        cursor.execute("SELECT slot_id, slot_name FROM group_slots WHERE group_id IS NULL AND admin_user_id = %s", (admin_user_id,))
    existing_slots = {row[1]: row[0] for row in cursor.fetchall()}  # slot_name -> slot_id

    # Track which slots we've processed
    processed_slot_names = set()

    for slot_data in slots_data:
        slot_name = slot_data.get('name', '').strip()
        if not slot_name:
            continue

        processed_slot_names.add(slot_name)

        # Handle image data - if it's Base64, save as file
        image_data = slot_data.get('image', '')
        if image_data and image_data.startswith('data:image/'):
            image_file_path = save_base64_image(image_data, admin_user_id, slot_name)
        else:
            image_file_path = image_data

        slot_config = {
            'group_id': group_id,
            'admin_user_id': admin_user_id,
            'event_id': event_id,
            'slot_name': slot_name,
            'start_time': slot_data.get('startTime', ''),
            'end_time': slot_data.get('endTime', ''),
            'initial_message': slot_data.get('botResponse', ''),
            'response_positive': slot_data.get('postResponse', ''),
            'image_file_path': image_file_path,
            'slot_points': slot_data.get('points', 0),
            'is_mandatory': slot_data.get('compulsory', False),
            'slot_type': 'button' if slot_data.get('type') == 'button' else 'default',
            'button_count': slot_data.get('buttonCount', 0),
            'button_names': json.dumps(slot_data.get('buttonNames', [])),
            'button_values': json.dumps(slot_data.get('buttonValues', []))
        }

        if slot_name in existing_slots:
            # Update existing slot
            update_slot(cursor, existing_slots[slot_name], slot_config)
        else:
            # Create new slot
            create_slot(cursor, slot_config)

    # Remove slots that are no longer in the configuration
    slots_to_remove = set(existing_slots.keys()) - processed_slot_names
    for slot_name in slots_to_remove:
        cursor.execute("DELETE FROM group_slots WHERE slot_id = %s", (existing_slots[slot_name],))


def create_slot(cursor, slot_config):
    """Create a new slot"""
    query = """
        INSERT INTO group_slots (
            group_id, admin_user_id, event_id, slot_name, start_time, end_time, initial_message,
            response_positive, response_clarify, image_file_path, slot_points, is_mandatory, slot_type,
            button_count, button_names, button_values
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        slot_config['group_id'], slot_config['admin_user_id'], slot_config['event_id'], slot_config['slot_name'],
        slot_config['start_time'], slot_config['end_time'], slot_config['initial_message'],
        slot_config['response_positive'], '',  # response_clarify is empty for now
        slot_config['image_file_path'], slot_config['slot_points'], slot_config['is_mandatory'], 
        slot_config['slot_type'], slot_config['button_count'], slot_config['button_names'], slot_config['button_values']
    )
    cursor.execute(query, params)


def update_slot(cursor, slot_id, slot_config):
    """Update an existing slot"""
    query = """
        UPDATE group_slots SET
            event_id = %s, slot_name = %s, start_time = %s, end_time = %s,
            initial_message = %s, response_positive = %s, response_clarify = %s,
            image_file_path = %s, slot_points = %s, is_mandatory = %s, slot_type = %s,
            button_count = %s, button_names = %s, button_values = %s
        WHERE slot_id = %s
    """
    params = (
        slot_config['event_id'], slot_config['slot_name'], slot_config['start_time'],
        slot_config['end_time'], slot_config['initial_message'], slot_config['response_positive'],
        '', slot_config['image_file_path'], slot_config['slot_points'], slot_config['is_mandatory'],  # response_clarify empty
        slot_config['slot_type'], slot_config['button_count'], slot_config['button_names'], 
        slot_config['button_values'], slot_id
    )
    cursor.execute(query, params)


def get_admin_panel_config(group_id):
    """
    Get current admin panel configuration for a group.
    Returns data in the format expected by the frontend.
    """
    try:
        # Get group config
        group_config = get_group_config(group_id)
        if not group_config:
            return None

        # Get event
        event_query = "SELECT * FROM events WHERE group_id = %s AND is_active = TRUE ORDER BY event_id DESC LIMIT 1"
        event_result = execute_query(event_query, (group_id,), fetch=True)
        event = event_result[0] if event_result else None

        # Get slots
        slots = get_all_slots(group_id)

        # Get banned words (global for now, group_id = NULL)
        banned_words_query = "SELECT word FROM banned_words WHERE group_id IS NULL ORDER BY word"
        banned_words_result = execute_query(banned_words_query, (), fetch=True)
        banned_words_string = ', '.join([row['word'] for row in banned_words_result]) if banned_words_result else ''

        # Format response
        config = {
            'group_id': group_id,
            'welcome_message': group_config.get('welcome_message', ''),
            'kick_response': group_config.get('kick_message', ''),
            'undesignated_slot_response': group_config.get('undesignated_slot_response', ''),
            'leaderboard_time': str(group_config.get('leaderboard_time', '')) if group_config.get('leaderboard_time') else '',
            'banned_words': banned_words_string,
            'max_members': group_config.get('max_members', 100),
            'event_name': event.get('event_name', 'Wellness Challenge') if event else 'Wellness Challenge',
            'event_type': event.get('event_type', 'normal') if event else 'normal',
            'event_days': event.get('event_days', 0) if event else 0,
            'slots_per_day': event.get('slots_per_day', 0) if event else 0,
            'pass_points': event.get('min_pass_points', 250) if event else 250,
            'slots': []
        }

        # Format slots
        for slot in slots:
            config['slots'].append({
                'name': slot.get('slot_name', ''),
                'compulsory': slot.get('is_mandatory', False),
                'startTime': str(slot.get('start_time', '')),
                'endTime': str(slot.get('end_time', '')),
                'points': slot.get('slot_points', 0),
                'type': 'button' if slot.get('slot_type') == 'button' else 'media',
                'botResponse': slot.get('initial_message', ''),
                'postResponse': slot.get('response_positive', ''),
                'image': slot.get('image_file_path', ''),
                'buttonCount': slot.get('button_count', 0),
                'buttonNames': json.loads(slot.get('button_names', '[]')) if slot.get('button_names') else [],
                'buttonValues': json.loads(slot.get('button_values', '[]')) if slot.get('button_values') else []
            })

        return config

    except Exception as e:
        logger.error(f"Error getting admin panel config: {e}", exc_info=True)
        return None


def save_banned_words(cursor, group_id, banned_words):
    """Save banned words to the banned_words table"""
    try:
        # For now, banned words are global (group_id = NULL)

        # Process the banned words array
        if banned_words and isinstance(banned_words, list) and len(banned_words) > 0:
            # Filter out empty strings and strip whitespace
            words = [word.strip() for word in banned_words if word.strip()]

            # Remove duplicates
            words = list(set(words))

            # Insert each word with group_id = NULL
            for word in words:
                cursor.execute(
                    "INSERT INTO banned_words (group_id, word) VALUES (NULL, %s)",
                    (word,)
                )

        logger.info(f"Saved {len(words) if 'words' in locals() else 0} global banned words")

    except Exception as e:
        logger.error(f"Error saving banned words: {e}")
        raise


def save_admin_panel_config(admin_user_id, group_id, config_data):
    """Save admin panel configuration"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Start transaction
            connection.start_transaction()

            try:
                # Save group configuration
                update_group_config(cursor, group_id, admin_user_id, config_data)

                # Only save events and slots if we have a specific group_id
                # (not for admin templates where group_id is None)
                if group_id is not None:
                    # Save event and slots
                    event_id = save_or_update_event(cursor, group_id, config_data)
                    save_or_update_slots(cursor, group_id, admin_user_id, event_id, config_data.get('slots', []))

                # Save banned words (always global for now)
                banned_words = config_data.get('banned_words', [])
                if banned_words:
                    save_banned_words(cursor, group_id, banned_words)

                # Commit transaction
                connection.commit()
                logger.info(f"Saved admin panel config for admin {admin_user_id}, group {group_id}")

                return True

            except Exception as e:
                connection.rollback()
                logger.error(f"Error saving admin panel config: {e}")
                raise

    except Exception as e:
        logger.error(f"Error in save_admin_panel_config: {e}")
        return False


def create_group_config(group_id, admin_user_id):
    """Create initial group configuration when bot joins a group"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Start transaction
            connection.start_transaction()

            try:
                # Insert group config
                query = """
                    INSERT INTO groups_config (group_id, admin_user_id, max_members, welcome_message, kick_message, undesignated_slot_response, leaderboard_time)
                    VALUES (%s, %s, 100, 'Welcome to our wellness group! 🎉', 'Please follow the group rules.', 'This is not a designated time slot. Please post during your assigned time slots.', '22:00:00')
                """
                cursor.execute(query, (group_id, admin_user_id))

                # Create default event
                event_query = """
                    INSERT INTO events (group_id, event_name, event_type, event_days, slots_per_day, start_date, end_date, min_pass_points, is_active)
                    VALUES (%s, 'Wellness Challenge', 'normal', 0, 9, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 365 DAY), 250, TRUE)
                """
                cursor.execute(event_query, (group_id,))

                event_id = cursor.lastrowid

                # Create default time slots
                default_slots = [
                    ('Breakfast', '06:00:00', '08:00:00', 'Good morning! 🌅 Time for breakfast. What healthy meal are you having?', 'Great breakfast choice! Keep up the healthy eating! 🥑'),
                    ('Morning Workout', '08:00:00', '10:00:00', 'Morning workout time! 💪 What exercise are you doing today?', 'Excellent workout! Your dedication is inspiring! 💪'),
                    ('Mid-Morning Snack', '10:00:00', '12:00:00', 'Healthy snack time! 🥕 What nutritious snack are you enjoying?', 'Perfect snack choice! Keep fueling your body! 🥦'),
                    ('Lunch', '12:00:00', '14:00:00', 'Lunchtime! 🥗 What balanced meal are you having?', 'Wonderful lunch choice! Nutrition is key! 🥙'),
                    ('Afternoon Workout', '14:00:00', '16:00:00', 'Afternoon exercise time! 🏃‍♀️ What activity are you doing?', 'Fantastic workout! You\'re doing amazing! 🏃‍♂️'),
                    ('Evening Snack', '16:00:00', '18:00:00', 'Evening snack time! 🍎 What healthy option are you choosing?', 'Great snack choice! Keep those healthy habits! 🍇'),
                    ('Dinner', '18:00:00', '20:00:00', 'Dinnertime! 🥘 What nutritious meal are you preparing?', 'Excellent dinner choice! You\'re crushing your goals! 🥘'),
                    ('Evening Walk', '20:00:00', '22:00:00', 'Evening walk time! 🚶‍♀️ How far are you walking today?', 'Wonderful walk! Movement is medicine! 🚶‍♂️'),
                    ('Good Night', '22:00:00', '23:59:00', 'Wind down time! 😴 What wellness activity are you doing before bed?', 'Perfect way to end the day! Sweet dreams! 😴')
                ]

                for slot_name, start_time, end_time, initial_msg, positive_msg in default_slots:
                    slot_query = """
                        INSERT INTO group_slots (group_id, admin_user_id, event_id, slot_name, start_time, end_time, initial_message, response_positive, response_clarify, slot_points, is_mandatory, slot_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, '', 10, FALSE, 'default')
                    """
                    cursor.execute(slot_query, (group_id, admin_user_id, event_id, slot_name, start_time, end_time, initial_msg, positive_msg))

                # Commit transaction
                connection.commit()
                logger.info(f"Created default configuration for group {group_id}")
                return True

            except Exception as e:
                connection.rollback()
                logger.error(f"Error creating group config: {e}")
                raise

    except Exception as e:
        logger.error(f"Error in create_group_config: {e}")
        return False