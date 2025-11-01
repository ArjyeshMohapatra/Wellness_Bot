from .utils import execute_query, logger, json, to_int_or_none, to_str_or_none, get_db_connection


def get_admin_bot_settings(admin_user_id):
    """
    Get all bot settings for an admin across all groups.
    Returns a list of settings objects, each representing a group's configuration.
    """
    try:
        query = """
            SELECT
                bs.*,
                gc.group_id,
                gc.group_name,
                e.license_key,
                e.admin_user_id
            FROM bot_settings bs
            JOIN groups_config gc ON bs.setting_id = gc.setting_id
            JOIN events e ON bs.event_id = e.event_id
            WHERE e.admin_user_id = %s AND bs.is_active = TRUE AND gc.is_active = TRUE
            ORDER BY gc.group_id
        """
        result = execute_query(query, (admin_user_id,), fetch=True)

        if not result:
            return []

        settings_list = []
        for row in result:
            settings = {
                'setting_id': row['setting_id'],
                'event_id': row['event_id'],
                'admin_user_id': row['admin_user_id'],
                'group_id': row['group_id'],
                'group_name': row['group_name'] if row['group_name'] else f"Group {row['group_id']}",
                'license_key': row['license_key'],
                'bot_username': row['bot_username'],
                'has_admin_permissions': row['has_admin_permissions'],
                'event_type': row['event_type'],
                'event_name': row['event_name'],
                'event_days': row['event_days'],
                'pass_points': row['pass_points'],
                'slots_per_day': row['slots_per_day'],
                'welcome_message': row['welcome_message'],
                'kick_response': row['kick_response'],
                'undesignated_slot_response': row['undesignated_slot_response'],
                'leaderboard_time': row['leaderboard_time'],
                'banned_words': json.loads(row['banned_words']) if row['banned_words'] else [],
                'loaded_slots': json.loads(row['loaded_slots']) if row['loaded_slots'] else [],
                'is_active': row['is_active'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            settings_list.append(settings)

        return settings_list

    except Exception as e:
        logger.error(f"Error getting admin bot settings: {e}", exc_info=True)
        return []


def get_bot_settings_for_event(event_id):
    """
    Get bot settings for a specific event.
    This is more reliable than get_bot_settings_for_group since it doesn't depend on setting_id linkage.
    """
    try:
        query = "SELECT * FROM bot_settings WHERE event_id = %s AND is_active = TRUE"
        result = execute_query(query, (event_id,), fetch=True)

        if not result:
            return None

        row = result[0]
        # Parse JSON fields
        banned_words = json.loads(row['banned_words']) if row['banned_words'] else []
        loaded_slots = json.loads(row['loaded_slots']) if row['loaded_slots'] else []

        settings = {
            'setting_id': row['setting_id'],
            'event_id': row['event_id'],
            'bot_username': row['bot_username'],
            'has_admin_permissions': row['has_admin_permissions'],
            'event_type': row['event_type'],
            'event_name': row['event_name'],
            'event_days': row['event_days'],
            'pass_points': row['pass_points'],
            'slots_per_day': row['slots_per_day'],
            'welcome_message': row['welcome_message'],
            'kick_response': row['kick_response'],
            'undesignated_slot_response': row['undesignated_slot_response'],
            'leaderboard_time': row['leaderboard_time'],
            'banned_words': banned_words,
            'loaded_slots': loaded_slots,
            'is_active': row['is_active'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }

        return settings

    except Exception as e:
        logger.error(f"Error getting bot settings for event {event_id}: {e}", exc_info=True)
        return None


def get_bot_settings_for_group(admin_user_id, group_id):
    """
    Get bot settings for a specific group.
    Returns the settings object for the group or None if not found.
    """
    try:
        query = """
            SELECT
                bs.*,
                gc.group_id,
                gc.group_name,
                e.license_key,
                e.admin_user_id
            FROM bot_settings bs
            JOIN groups_config gc ON bs.setting_id = gc.setting_id
            JOIN events e ON bs.event_id = e.event_id
            WHERE e.admin_user_id = %s AND gc.group_id = %s AND bs.is_active = TRUE AND gc.is_active = TRUE
        """
        result = execute_query(query, (admin_user_id, group_id), fetch=True)

        if not result:
            return None

        row = result[0]
        settings = {
            'setting_id': row['setting_id'],
            'event_id': row['event_id'],
            'admin_user_id': row['admin_user_id'],
            'group_id': row['group_id'],
            'group_name': row['group_name'] if row['group_name'] else f"Group {row['group_id']}",
            'license_key': row['license_key'],
            'bot_username': row['bot_username'],
            'has_admin_permissions': row['has_admin_permissions'],
            'event_type': row['event_type'],
            'event_name': row['event_name'],
            'event_days': row['event_days'],
            'pass_points': row['pass_points'],
            'slots_per_day': row['slots_per_day'],
            'welcome_message': row['welcome_message'],
            'kick_response': row['kick_response'],
            'undesignated_slot_response': row['undesignated_slot_response'],
            'leaderboard_time': row['leaderboard_time'],
            'banned_words': json.loads(row['banned_words']) if row['banned_words'] else [],
            'loaded_slots': json.loads(row['loaded_slots']) if row['loaded_slots'] else [],
            'is_active': row['is_active'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }

        return settings

    except Exception as e:
        logger.error(f"Error getting bot settings for group: {e}", exc_info=True)
        return None


def save_bot_settings_for_group(admin_user_id, group_id, settings):
    """
    Save or update bot settings for a specific group.
    This function handles the relationship between events, bot_settings, and groups_config.
    Returns True on success, False on failure.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Start transaction
                conn.start_transaction()

                # Prepare the data
                license_key = settings.get('license_key')
                bot_username = settings.get('bot_username', 'WellnessBot')
                has_admin_permissions = settings.get('has_admin_permissions', False)
                event_type = settings.get('event_type', 'normal')
                event_name = settings.get('event_name', 'Wellness Event')
                event_days = to_int_or_none(settings.get('event_days', 7))
                pass_points = to_int_or_none(settings.get('pass_points', 250))
                slots_per_day = to_int_or_none(settings.get('slots_per_day', 2))
                welcome_message = settings.get('welcome_message', 'Welcome to our wellness program!')
                kick_response = settings.get('kick_response', 'You have been removed for not following the rules.')
                undesignated_slot_response = settings.get('undesignated_slot_response', 'Please respond to your assigned slot.')
                leaderboard_time = to_str_or_none(settings.get('leaderboard_time', '11:00'))
                banned_words = json.dumps(settings.get('banned_words', []))
                loaded_slots = json.dumps(settings.get('loaded_slots', []))

                # First, find or create the event
                event_id = None
                if license_key:
                    # Check if event already exists with this license_key
                    cursor.execute("SELECT event_id FROM events WHERE license_key = %s",
                                 (license_key,))
                    existing_event = cursor.fetchone()
                    if existing_event:
                        event_id = existing_event[0]
                    else:
                        # Create new event
                        cursor.execute("""
                            INSERT INTO events (admin_user_id, event_name, event_type, event_days, slots_per_day,
                                              start_date, end_date, min_pass_points, license_key)
                            VALUES (%s, %s, %s, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL %s DAY), %s, %s)
                        """, (admin_user_id, event_name, event_type, event_days, slots_per_day, event_days, pass_points, license_key))
                        event_id = cursor.lastrowid

                        # Insert license into licenses table
                        cursor.execute("""
                            INSERT INTO licenses (license_key, event_id, is_active, assigned_admin_id)
                            VALUES (%s, %s, TRUE, %s)
                        """, (license_key, event_id, admin_user_id))

                if not event_id:
                    logger.error("Could not find or create event")
                    return False

                # Save bot settings for the event
                query = """
                    INSERT INTO bot_settings
                    (event_id, bot_username, has_admin_permissions, event_type, event_name,
                     event_days, pass_points, slots_per_day, welcome_message, kick_response,
                     undesignated_slot_response, leaderboard_time, banned_words, loaded_slots, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                    ON DUPLICATE KEY UPDATE
                        bot_username = VALUES(bot_username),
                        has_admin_permissions = VALUES(has_admin_permissions),
                        event_type = VALUES(event_type),
                        event_name = VALUES(event_name),
                        event_days = VALUES(event_days),
                        pass_points = VALUES(pass_points),
                        slots_per_day = VALUES(slots_per_day),
                        welcome_message = VALUES(welcome_message),
                        kick_response = VALUES(kick_response),
                        undesignated_slot_response = VALUES(undesignated_slot_response),
                        leaderboard_time = VALUES(leaderboard_time),
                        banned_words = VALUES(banned_words),
                        loaded_slots = VALUES(loaded_slots),
                        updated_at = CURRENT_TIMESTAMP
                """

                params = (
                    event_id, bot_username, has_admin_permissions, event_type, event_name,
                    event_days, pass_points, slots_per_day, welcome_message, kick_response,
                    undesignated_slot_response, leaderboard_time, banned_words, loaded_slots
                )

                try:
                    cursor.execute(query, params)
                    setting_id = cursor.lastrowid
                except Exception as e:
                    logger.error(f"Failed executing save_bot_settings. Query: {query} | Params: {params} | Error: {e}", exc_info=True)
                    raise

                # Save groups_config
                cursor.execute("""
                    INSERT INTO groups_config
                    (group_id, event_id, admin_user_id, setting_id, has_admin_permissions, is_active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    ON DUPLICATE KEY UPDATE
                        event_id = VALUES(event_id),
                        setting_id = VALUES(setting_id),
                        has_admin_permissions = VALUES(has_admin_permissions),
                        is_active = TRUE
                """, (group_id, event_id, admin_user_id, setting_id, has_admin_permissions))

                # Commit transaction
                conn.commit()

                logger.info(f"Successfully saved bot settings for admin {admin_user_id}, group {group_id}, event {event_id}")
                return True

    except Exception as e:
        logger.error(f"Error saving bot settings for group: {e}", exc_info=True)
        return False