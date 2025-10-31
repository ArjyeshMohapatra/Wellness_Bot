from .utils import get_db_connection, logger
from .group_config import update_group_config
from .events_slots import save_or_update_event, save_or_update_slots
from .banned_words import save_banned_words
from generate_license import generate_license_key


def create_event(cursor, admin_user_id, config_data, license_key):
    """Create a new event"""
    event_name = config_data.get('event_name', 'Wellness Challenge')
    event_type = config_data.get('event_type', 'normal')
    event_days = int(config_data.get('event_days') or 7)
    slots_per_day = int(config_data.get('slots_per_day') or 2)
    pass_points = int(config_data.get('pass_points') or 250)

    # Calculate start and end dates
    from .utils import ist, datetime, timedelta
    start_date = datetime.now(ist).date()
    if event_type == 'time-limited' and event_days > 0:
        end_date = start_date + timedelta(days=event_days - 1)
    else:
        end_date = start_date + timedelta(days=365*10)  # 10 years

    query = """
        INSERT INTO events (admin_user_id, event_name, event_type, event_days, slots_per_day,
                           start_date, end_date, min_pass_points, license_key, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
    """
    params = (admin_user_id, event_name, event_type, event_days, slots_per_day,
             start_date, end_date, pass_points, license_key)
    cursor.execute(query, params)
    return cursor.lastrowid


def create_bot_settings(cursor, event_id, config_data):
    """Create bot settings for an event"""
    query = """
        INSERT INTO bot_settings (event_id, bot_username, has_admin_permissions, event_type, event_name,
                                 event_days, pass_points, slots_per_day, welcome_message, kick_response,
                                 undesignated_slot_response, leaderboard_time, banned_words, loaded_slots)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        event_id,
        config_data.get('bot_username', 'WellnessBot'),
        config_data.get('has_admin_permissions', False),
        config_data.get('event_type', 'normal'),
        config_data.get('event_name', ''),
        config_data.get('event_days', 7),
        config_data.get('pass_points', 250),
        config_data.get('slots_per_day', 2),
        config_data.get('welcome_message', ''),
        config_data.get('kick_response', ''),
        config_data.get('undesignated_slot_response', ''),
        config_data.get('leaderboard_time', '11:00'),
        config_data.get('banned_words', ''),
        config_data.get('loaded_slots', '[]')
    )
    cursor.execute(query, params)


def update_group_config_with_event(cursor, group_id, admin_user_id, event_id, config_data):
    """Update group config with event association"""
    query = """
        INSERT INTO groups_config (group_id, event_id, admin_user_id, max_members, welcome_message,
                                  kick_message, undesignated_slot_response, leaderboard_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        event_id = VALUES(event_id),
        admin_user_id = VALUES(admin_user_id),
        max_members = VALUES(max_members),
        welcome_message = VALUES(welcome_message),
        kick_message = VALUES(kick_message),
        undesignated_slot_response = VALUES(undesignated_slot_response),
        leaderboard_time = VALUES(leaderboard_time)
    """
    params = (
        group_id,
        event_id,
        admin_user_id,
        config_data.get('max_members', 0),
        config_data.get('welcome_message', ''),
        config_data.get('kick_response', ''),
        config_data.get('undesignated_slot_response', ''),
        config_data.get('leaderboard_time', '11:00')
    )
    cursor.execute(query, params)


def save_admin_panel_config(admin_user_id, group_id, config_data):
    """Save admin panel configuration"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Start transaction
            connection.start_transaction()

            try:
                # Generate license key for the event
                license_key = generate_license_key()

                # Create event
                event_id = create_event(cursor, admin_user_id, config_data, license_key)

                # Create bot settings for the event
                create_bot_settings(cursor, event_id, config_data)

                # If group_id is provided, associate with group
                if group_id is not None and group_id != 0:
                    update_group_config_with_event(cursor, group_id, admin_user_id, event_id, config_data)

                # Note: Slots are now saved via the API when saving bot settings

                # Save banned words (global for now)
                banned_words = config_data.get('banned_words', [])
                if banned_words:
                    save_banned_words(cursor, group_id, banned_words)

                # Insert into licenses table
                cursor.execute(
                    "INSERT INTO licenses (license_key, event_id, assigned_admin_id) VALUES (%s, %s, %s)",
                    (license_key, event_id, admin_user_id)
                )

                # Commit transaction
                connection.commit()
                logger.info(f"Saved admin panel config for admin {admin_user_id}, event {event_id}")

                return True, license_key, event_id

            except Exception as e:
                connection.rollback()
                logger.error(f"Error saving admin panel config: {e}")
                raise

    except Exception as e:
        logger.error(f"Error in save_admin_panel_config: {e}")
        return False, None, None

