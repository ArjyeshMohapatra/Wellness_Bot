import logging
from datetime import datetime, date, timedelta, time

from db import execute_query, get_db_connection

logger = logging.getLogger(__name__)

def get_group_config(group_id):
    query = "SELECT * FROM groups_config WHERE group_id = %s"
    result = execute_query(query, (group_id,), fetch=True)
    return result[0] if result else None

def create_group_config(group_id, admin_user_id):
        try:
            # Check if group config already exists
            existing_config = get_group_config(group_id)
            
            if not existing_config:
                license_key = f"AUTO_{group_id}_{int(datetime.now().timestamp())}"
                
                execute_query(
                    "INSERT INTO licenses (license_key, is_active, assigned_group_id, assigned_admin_id) VALUES (%s, TRUE, %s, %s)",
                    (license_key, group_id, admin_user_id)
                )
                
                execute_query("""
                    INSERT INTO groups_config 
                    (group_id, license_key, admin_user_id, max_members, welcome_message, kick_message)
                    VALUES (%s, %s, %s, 100, 'Welcome! 🌟', 'Goodbye!')
                """, (group_id, license_key, admin_user_id))
                
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
            
            with get_db_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                # Create a 7-day ongoing wellness event
                start_date = datetime.now().date()
                end_date = start_date + timedelta(days=7)
                
                cursor.execute("""
                    INSERT INTO events 
                    (group_id, event_name, start_date, end_date, min_pass_points, is_active)
                    VALUES (%s, 'Wellness Challenge', %s, %s, 250, TRUE)
                """, (group_id, start_date, end_date))
                
                event_id = cursor.lastrowid
                logger.info(f"Created wellness event {event_id} for group {group_id}")
                
                # Create 8 default slots with all response fields
                slots = [
                    ('Good Morning', '10:15:00', '10:17:00', 'text', 10, 10, 
                     'Its Good morning everyone! Share your morning photo 🌅',
                     'Great start to your day! ✅',
                     'Is this for the Good Morning slot?'),
                    
                    ('Workout', '10:17:00', '10:19:00', 'photo', 10, 10, 
                     'Its Workout time everyone! Post your exercise photo 💪',
                     'Amazing workout! 💪',
                     'Is this for the Workout slot?'),
                    
                    ('Breakfast', '10:19:00', '10:21:00', 'photo', 10, 10, 
                     'Its Breakfast time everyone! Share your delicious & healthy meal 🍳',
                     'Healthy breakfast! 🍳',
                     'Is this for the Breakfast slot?'),
                    
                    ('Morning Water Intake', '10:21:00', '10:23:00', 'button', 2, 0, 
                     'Lets checkout your morning hydration everyone! How much water did everyone drink ? 💧',
                     'Great hydration! 💧',
                     'Did you drink water?'),
                    
                    ('Lunch', '10:23:00', '10:25:00', 'photo', 10, 10, 
                     'Its Lunch time everyone! Post your delicious meal 🍱',
                     'Nutritious lunch! 🍱',
                     'Is this for the Lunch slot?'),
                    
                    ('Afternoon Water Intake', '10:25:00', '10:27:00', 'button', 2, 0, 
                     'Lets checkout your afternoon hydration everyone! How much water did everyone drink ? 💧',
                     'Great hydration! 💧',
                     'Did you drink water?'),
                    
                    ('Evening Snacks', '10:27:00', '10:29:00', 'photo', 10, 10, 
                     'Evening snack time! Share your healthy snack 🍎',
                     'Healthy snack! 🍎',
                     'Is this for the Evening Snacks slot?'),
                    
                    ('Evening Water intake', '10:29:00', '10:31:00', 'button', 2, 0, 
                     'Lets checkout how hydrated are you in evening! Track your water 💧',
                     'Great hydration! 💧',
                     'Did you drink water?'),
                    
                    ('Dinner', '10:31:00', '10:33:00', 'photo', 10, 10, 
                     'Its Dinner time everyone! Share your healthy meal 🍽️',
                     'Delicious dinner! 🍽️',
                     'Is this for the Dinner slot?')
                ]
                
                # Multilingual keywords for each slot
                slot_keywords = {
                    'Good Morning': ['good morning','morning'],
                    'Workout': [],
                    'Breakfast': ['breakfast','morning meal'],
                    'Morning Water Intake': [],
                    'Lunch': ['lunch','afternoon meal'],
                    'Afternoon Water Intake': [],
                    'Evening Snacks': ['snacks', 'evening snack'],
                    'Evening Water Intake': [],
                    'Dinner': ['dinner','night meal']
                }
                
                for slot_name, start_time, end_time, slot_type, pts_text, pts_photo, initial_msg, response_pos, response_clar in slots:
                    is_mandatory = 0 if slot_name == 'Evening Snacks' else 1
                    
                    cursor.execute("""
                        INSERT INTO group_slots 
                        (group_id, slot_name, start_time, end_time, slot_type, points_for_text, points_for_photo, 
                         initial_message, response_positive, response_clarify, is_mandatory)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (group_id, slot_name, start_time, end_time, slot_type, pts_text, pts_photo, 
                          initial_msg, response_pos, response_clar, is_mandatory))
                    
                    slot_id = cursor.lastrowid
                    
                    # Add keywords for this slot
                    if slot_name in slot_keywords:
                        for keyword in slot_keywords[slot_name]:
                            cursor.execute("""
                                INSERT INTO slot_keywords (slot_id, keyword)
                                VALUES (%s, %s)
                            """, (slot_id, keyword))
                
                cursor.close()
                conn.commit()
                logger.info(f"Created {len(slots)} default slots with multilingual keywords for group {group_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error creating default slots: {e}")
            return False
    
def add_member(group_id, user_id, username=None, first_name=None):
        try:
            # Check if member already exists
            existing = get_member(group_id, user_id)
            
            if existing:
                # Update existing member
                query = """
                    UPDATE group_members 
                    SET username = %s, first_name = %s, last_active_timestamp = NOW()
                    WHERE group_id = %s AND user_id = %s
                """
                execute_query(query, (username, first_name, group_id, user_id))
            else:
                # New member - check if admin (admins never get restricted)
                group_config = get_group_config(group_id)
                is_admin = (group_config and group_config.get('admin_user_id') == user_id)
                
                if is_admin:
                    # Admin - no restriction ever
                    is_restricted = 0
                    logger.info(f"Admin {user_id} added to group {group_id} - NO RESTRICTION (admin privilege)")
                else:
                    # Regular member - check if joining during active slot (mid-day)
                    active_slot = get_active_slot(group_id)
                    
                    # Get the first slot time from database
                    all_slots = get_all_slots(group_id)
                    if all_slots and len(all_slots) > 0:
                        first_slot_start = all_slots[0]['start_time']
                        if hasattr(first_slot_start, 'total_seconds'):
                            first_slot_start = (datetime.min + first_slot_start).time()
                    else:
                        first_slot_start = time(4, 0)  # Default fallback
                    
                    current_time = datetime.now().time()
                    
                    is_restricted = 1 if active_slot else 0
                
                query = """
                    INSERT INTO group_members 
                    (user_id, group_id, username, first_name, user_day_number, cycle_start_date, is_restricted, last_active_timestamp, joined_at)
                    VALUES (%s, %s, %s, %s, 1, CURDATE(), %s, NOW(), NOW())
                """
                execute_query(query, (user_id, group_id, username, first_name, is_restricted))
                
                if is_restricted:
                    logger.info(f"New member {user_id} added to group {group_id} - RESTRICTED until tomorrow (joined mid-day)")
                else:
                    logger.info(f"New member {user_id} added to group {group_id} - Day 1 cycle started immediately")
                
                execute_query(
                    "INSERT INTO member_history (group_id, user_id, action) VALUES (%s, %s, 'joined')",
                    (group_id, user_id)
                )
            
            return True
        except Exception as e:
            logger.error(f"Error adding member: {e}")
            return False
    
def update_member_activity(group_id, user_id):
        query = "UPDATE group_members SET last_active_timestamp = NOW() WHERE group_id = %s AND user_id = %s"
        execute_query(query, (group_id, user_id))
    
def get_member(group_id, user_id):
        query = "SELECT * FROM group_members WHERE group_id = %s AND user_id = %s"
        result = execute_query(query, (group_id, user_id), fetch=True)
        return result[0] if result else None
    
def add_warning(group_id, user_id):
        # Use banned_word_count as warning counter since 'warnings' column doesn't exist
        query = "UPDATE group_members SET banned_word_count = banned_word_count + 1 WHERE group_id = %s AND user_id = %s"
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
            logger.info(f"Deducted {points} knockout points from user {user_id} in group {group_id}")
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
    
def remove_member(group_id, user_id, action='kicked'):
        try:
            execute_query(
                "INSERT INTO member_history (group_id, user_id, action) VALUES (%s, %s, %s)",
                (group_id, user_id, action)
            )
            
            # Delete member
            execute_query("DELETE FROM group_members WHERE group_id = %s AND user_id = %s", (group_id, user_id))
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
        return [r['keyword'] for r in results] if results else []
    
def log_activity(group_id, user_id, slot_name, activity_type, message_content=None, 
                    telegram_file_id=None, local_file_path=None, points_earned=0, is_valid=True):
        query = """
            INSERT INTO user_activity_log 
            (group_id, user_id, slot_name, activity_type, message_content, 
             telegram_file_id, local_file_path, points_earned, is_valid)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(query, (group_id, user_id, slot_name, activity_type, message_content,
                             telegram_file_id, local_file_path, points_earned, is_valid))
    
def add_points(group_id, user_id, points, event_id=None):
        try:
            query = "UPDATE group_members SET current_points = current_points + %s WHERE group_id = %s AND user_id = %s"
            execute_query(query, (points, group_id, user_id))
            
            if event_id:
                log_query = """
                    INSERT INTO daily_points_log (event_id, user_id, log_date, points_scored)
                    VALUES (%s, %s, CURDATE(), %s)
                    ON DUPLICATE KEY UPDATE points_scored = points_scored + VALUES(points_scored)
                """
                execute_query(log_query, (event_id, user_id, points))
            
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
    
def mark_slot_completed(event_id, slot_id, user_id, status='completed'):
        query = """
            INSERT INTO daily_slot_tracker (event_id, slot_id, user_id, log_date, status)
            VALUES (%s, %s, %s, CURDATE(), %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status), duplicate_submissions = duplicate_submissions + 1
        """
        execute_query(query, (event_id, slot_id, user_id, status))
    
def check_slot_completed_today(event_id, slot_id, user_id):
        query = """
            SELECT COUNT(*) as count FROM daily_slot_tracker
            WHERE event_id = %s AND slot_id = %s AND user_id = %s 
            AND log_date = CURDATE() AND status = 'completed'
        """
        result = execute_query(query, (event_id, slot_id, user_id), fetch=True)
        return result[0]['count'] > 0 if result else False
    
def get_banned_words(group_id):
        query = "SELECT word FROM banned_words WHERE group_id = %s OR group_id IS NULL"
        results = execute_query(query, (group_id,), fetch=True)
        return [r['word'] for r in results] if results else []
    
def get_leaderboard(group_id, limit=10):
        query = """
            SELECT user_id, username, first_name, current_points, knockout_points, user_day_number,
                   (current_points - knockout_points) AS net_points
            FROM group_members
            WHERE group_id = %s
            ORDER BY net_points DESC
            LIMIT %s
        """
        return execute_query(query, (group_id, limit), fetch=True)
    

