import logging
from datetime import datetime, timedelta
from pytz import timezone
from config import NEW_MEMBER_RESTRICTION_MINUTES
from db import execute_query, get_db_connection

logger = logging.getLogger(__name__)


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
    ist = timezone("Asia/Kolkata")
    now_ist = datetime.now(ist)
    first_slot_timedelta = get_first_slot_time(group_id)

    if not first_slot_timedelta:
        # Fallback if no slots are defined: restrict for a few minutes.
        return (now_ist + timedelta(minutes=NEW_MEMBER_RESTRICTION_MINUTES)).replace(tzinfo=None)

    first_slot_time = (datetime.min + first_slot_timedelta).time()

    # Get the time of the first slot on today's date
    first_slot_today_ist = ist.localize(datetime.combine(now_ist.date(), first_slot_time))

    if now_ist < first_slot_today_ist:
        # If the user joins BEFORE the first slot today, restrict them until that slot starts.
        return first_slot_today_ist.replace(tzinfo=None)
    else:
        # If the user joins AFTER the first slot today, restrict them until the first slot TOMORROW.
        tomorrow_date = (now_ist + timedelta(days=1)).date()
        first_slot_tomorrow_ist = ist.localize(datetime.combine(tomorrow_date, first_slot_time))
        return first_slot_tomorrow_ist.replace(tzinfo=None)


def create_group_config(group_id, admin_user_id):
    try:
        # Check if group config already exists
        existing_config = get_group_config(group_id)

        if not existing_config:
            license_key = f"AUTO_{group_id}_{int(datetime.now().timestamp())}"

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
        logger.error(f"Error creating group config: {e}")
        return False


def create_default_event_and_slots(group_id):
    try:
        # Check if slots already exist for this group
        existing_slots = get_all_slots(group_id)
        if existing_slots:
            logger.info(f"Slots already exist for group {group_id}, skipping creation")
            return True

        # Create a 7-day ongoing wellness event
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=7)
        
        query="""
                INSERT INTO events 
                (group_id, event_name, start_date, end_date, min_pass_points, is_active)
                VALUES (%s, 'Wellness Challenge', %s, %s, 250, TRUE)
            """
        event_id=execute_query(query,(group_id, start_date, end_date))

        logger.info(f"Created wellness event {event_id} for group {group_id}")

        slots = [
            ("Good Morning", "10:30:00", "10:35:00", "media", 10,
                "Its Good morning everyone! Share your morning photo 🌅",
                "Great start to your day! ✅", "Is this your Good Morning ?"),
            ("Workout", "10:40:00", "10:45:00", "media", 10,
                "Its Workout time everyone! Post your exercise photo 💪",
                "Amazing workout! 💪", "Is this your Workout ?"),
            ("Breakfast", "10:50:00", "10:55:00", "media", 10,
                "Its Breakfast time everyone! Share your delicious & healthy meal 🍳",
                "Healthy breakfast! 🍳", "Is this your Breakfast ?"),
            ("Morning Water Intake", "11:00:00", "11:05:00", "button", 10,
                "Lets checkout your morning hydration everyone! How much water did everyone drink ? 💧",
                "Great hydration! 💧", "Is this the amount of water you drank ?"),
            ("Lunch", "11:10:00", "11:15:00", "media", 10,
                "Its Lunch time everyone! Post your delicious meal 🍱",
                "Nutritious lunch! 🍱", "Is this your lunch ?"),
            ("Afternoon Water Intake", "11:20:00", "11:25:00", "button", 10,
                "Lets checkout your afternoon hydration everyone! How much water did everyone drink ? 💧",
                "Great hydration! 💧", "Is this the amount of water you drank ?"),
            ("Evening Snacks", "11:30:00", "11:35:00", "media",10,
                "Evening snack time! Share your healthy snack 🍎",
                "Healthy snack! 🍎", "Is this your evening snacks ?"),
            ("Evening Water intake", "11:40:00", "11:45:00", "button", 10,
                "Lets checkout how hydrated are you in evening! Track your water 💧",
                "Great hydration! 💧", "Is this the amount of water you drank ?"),
            ("Dinner", "11:50:00", "11:55:00", "media", 10,
                "Its Dinner time everyone! Share your healthy meal 🍽️",
                "Delicious dinner! 🍽️", "Is this your dinner ?"),
        ]

        slot_keywords = {
            "Good Morning": ["good morning", "morning"],
            "Workout": [],
            "Breakfast": ["breakfast", "morning meal"],
            "Morning Water Intake": [],
            "Lunch": ["lunch", "afternoon meal"],
            "Afternoon Water Intake": [],
            "Evening Snacks": ["snacks", "evening snack"],
            "Evening Water Intake": [],
            "Dinner": ["dinner", "night meal"],
        }

        for (slot_name,start_time,end_time,slot_type,slot_points,initial_msg,response_pos,response_clar) in slots:
            is_mandatory = 0 if slot_name == "Evening Snacks" else 1
            
            query="""
                    INSERT INTO group_slots 
                    (group_id, event_id, slot_name, start_time, end_time, 
                        initial_message, response_positive, response_clarify, image_file_path, slot_type, slot_points, is_mandatory)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            slot_id=execute_query(query,(group_id, event_id, slot_name,start_time,end_time,
                                    initial_msg,response_pos,response_clar, None, slot_type, slot_points, is_mandatory))

            # Add keywords for this slot
            if slot_name in slot_keywords:
                for keyword in slot_keywords[slot_name]:
                    query="""
                    INSERT INTO slot_keywords (slot_id, keyword) VALUES (%s, %s)
                    """
                    execute_query(query,(slot_id, keyword))
        logger.info(
            f"Created {len(slots)} default slots with multilingual keywords for group {group_id}"
        )
        return True

    except Exception as e:
        logger.error(f"Error creating default slots: {e}")
        return False


def add_member(group_id, user_id, username=None, first_name=None, last_name=None, is_admin=False):
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

        # Only calculate restriction for genuinely new members
        if is_new and not is_admin:
            is_restricted = 1
            restriction_until = get_restriction_until_time(group_id)
            if restriction_until is not None:
                restriction_until = restriction_until.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"🔒 DB: New member {user_id} marked for restriction until {restriction_until} (IST)")

        # handles both INSERT for new members and UPDATE for existing ones
        query = """
            INSERT INTO group_members (user_id, group_id, username, first_name, last_name, is_restricted, restriction_until, joined_at, last_active_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                first_name = VALUES(first_name),
                last_name = VALUES(last_name),
                last_active_timestamp = NOW()
        """
        execute_query(query, (user_id, group_id, username, first_name, last_name, is_restricted, restriction_until))

        # If they are new, also log to history
        if is_new:
            execute_query(
                "INSERT INTO member_history (group_id, user_id, username, first_name, last_name, action) VALUES (%s, %s, %s, %s, %s, 'joined')",
                (group_id, user_id, username, first_name, last_name),
            )
            logger.debug(f"[DEBUG] member_history INSERT complete for new user {user_id}")

        member_data = get_member(group_id, user_id)
        return member_data, is_new

    except Exception as e:
        logger.error(f"Error in add_member: {e}")
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
                    current_points = GREATEST(0, current_points - %s)
                WHERE group_id = %s AND user_id = %s
            """
        execute_query(query, (points, points, group_id, user_id))
        logger.info(
            f"Deducted {points} knockout points from user {user_id} in group {group_id}"
        )
        return True
    except Exception as e:
        logger.error(f"Error deducting knockout points: {e}")
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
    execute_query(query, (
        group_id, user_id,
        member_details.get('username'),
        member_details.get('first_name'),
        member_details.get('last_name'),
        warning_type
    ))

def remove_member(group_id, user_id, action="kicked"):
    try:
        # First, get the member's details BEFORE deleting them
        member = get_member(group_id, user_id)
        if member:
            username = member.get("username")
            first_name = member.get("first_name")
            last_name = member.get("last_name")
            
            # Now, log their details to the history table
            execute_query(
                "INSERT INTO member_history (group_id, user_id, username, first_name, last_name, action) VALUES (%s, %s, %s, %s, %s, %s)",
                (group_id, user_id, username, first_name, last_name, action),
            )
        else:
            # Fallback in case member is not found
            execute_query(
                "INSERT INTO member_history (group_id, user_id, action) VALUES (%s, %s, %s)",
                (group_id, user_id, action),
            )

        # Finally, delete the member from the main table
        execute_query(
            "DELETE FROM group_members WHERE group_id = %s AND user_id = %s",
            (group_id, user_id),
        )
        return True
    except Exception as e:
        logger.error(f"Error removing member: {e}")
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


def log_activity(
    group_id,
    user_id,
    activity_type,
    slot_name,
    username=None,
    first_name=None,
    last_name=None,
    message_content=None,
    telegram_file_id=None,
    local_file_path=None,
    points_earned=0,
    is_valid=True,
):
    query = """
            INSERT INTO user_activity_log 
            (group_id, user_id, activity_type, slot_name,username, first_name, last_name, message_content, 
             telegram_file_id, local_file_path, points_earned, is_valid)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    execute_query(
        query,
        (
            group_id,
            user_id,
            activity_type,
            slot_name,
            username,
            first_name,
            last_name,
            message_content,
            telegram_file_id,
            local_file_path,
            points_earned,
            is_valid,
        ),
    )


def add_points(group_id, user_id, points, event_id=None):
    try:
        query = "UPDATE group_members SET current_points = current_points + %s WHERE group_id = %s AND user_id = %s"
        execute_query(query, (points, group_id, user_id))

        if event_id:
            # Get member details to log them
            member = get_member(group_id, user_id)
            if member:
                log_query = """
                        INSERT INTO daily_points_log (event_id, user_id, username, first_name, last_name, log_date, points_scored)
                        VALUES (%s, %s, %s, %s, %s, CURDATE(), %s)
                        ON DUPLICATE KEY UPDATE points_scored = points_scored + VALUES(points_scored)
                    """
                execute_query(log_query, (event_id, user_id, member.get('username'), member.get('first_name'), member.get('last_name'), points))

        return True
    except Exception as e:
        logger.error(f"Error adding points: {e}")
        return False

def get_low_point_members(group_id, min_points):
    query = """
            SELECT user_id, username, first_name, current_points
            FROM group_members
            WHERE group_id = %s AND current_points < %s
        """
    return execute_query(query, (group_id, min_points), fetch=True)


def mark_slot_completed(group_id, event_id, slot_id, user_id, status="completed"):
    """
    Attempts to mark a slot as completed.
    Returns True if a new row was inserted (first completion).
    Returns False if the row already existed (duplicate submission).
    """
    member = get_member(group_id, user_id)

    if member:
        username = member.get('username')
        first_name = member.get('first_name')
        last_name = member.get('last_name')
    else:
        username, first_name, last_name = None, None, None

    query = """
            INSERT INTO daily_slot_tracker (event_id, slot_id, user_id, username, first_name, last_name, log_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s)
            ON DUPLICATE KEY UPDATE duplicate_submissions = duplicate_submissions + 1
        """
        
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, (event_id, slot_id, user_id, username, first_name, last_name, status))
            # cursor.rowcount == 1 means a new row was inserted.
            # cursor.rowcount == 2 means an existing row was updated.
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
            SELECT user_id, username, first_name, current_points, knockout_points, user_day_number,
                   (current_points - knockout_points) AS net_points
            FROM group_members
            WHERE group_id = %s AND (current_points - knockout_points) > 0
            ORDER BY net_points DESC
            LIMIT %s
        """
    return execute_query(query, (group_id, limit), fetch=True)
