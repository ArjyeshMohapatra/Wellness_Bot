from .utils import execute_query, logger, json, to_int_or_none, to_str_or_none


def save_admin_dashboard_settings(admin_user_id, settings):
    """Save admin dashboard settings to database."""
    try:
        print(f"DB: Saving dashboard settings for admin {admin_user_id}: {settings}")
        query = """
        INSERT INTO admin_dashboard_settings
        (admin_user_id, bot_username, has_admin_permissions, license_key, loaded_slots,
         event_type, event_name, event_days, pass_points, slots_per_day,
         welcome_message, kick_response, undesignated_slot_response, leaderboard_time, banned_words)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        bot_username = VALUES(bot_username),
        has_admin_permissions = VALUES(has_admin_permissions),
        license_key = VALUES(license_key),
        loaded_slots = VALUES(loaded_slots),
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
        updated_at = CURRENT_TIMESTAMP
        """
        loaded_slots_json = json.dumps(settings.get('loaded_slots', [])) if settings.get('loaded_slots') else None
        banned_words_json = json.dumps(settings.get('banned_words', [])) if settings.get('banned_words') else None

        params = (
            admin_user_id,
            settings.get('bot_username', 'WellnessBot'),
            settings.get('has_admin_permissions', False),
            settings.get('license_key'),
            loaded_slots_json,
            settings.get('event_type', 'normal'),
            settings.get('event_name'),
            to_int_or_none(settings.get('event_days')),
            to_int_or_none(settings.get('pass_points')),
            to_int_or_none(settings.get('slots_per_day')),
            settings.get('welcome_message'),
            settings.get('kick_response'),
            settings.get('undesignated_slot_response'),
            to_str_or_none(settings.get('leaderboard_time')),
            banned_words_json
        )
        print(f"DB: Executing query with params: {params}")
        execute_query(query, params)
        print(f"DB: Successfully saved dashboard settings for admin {admin_user_id}")
        return True
    except Exception as e:
        print(f"DB: Error saving admin dashboard settings: {e}")
        logger.error(f"Error saving admin dashboard settings: {e}", exc_info=True)
        return False


def get_admin_dashboard_settings(admin_user_id):
    """Get admin dashboard settings from database."""
    try:
        query = "SELECT * FROM admin_dashboard_settings WHERE admin_user_id = %s"
        result = execute_query(query, (admin_user_id,), fetch=True)
        if result:
            settings = result[0]
            if settings.get('loaded_slots'):
                settings['loaded_slots'] = json.loads(settings['loaded_slots'])
            if settings.get('banned_words'):
                settings['banned_words'] = json.loads(settings['banned_words'])
            return settings
        return None
    except Exception as e:
        logger.error(f"Error getting admin dashboard settings: {e}", exc_info=True)
        return None


def get_admin_bot_settings(admin_user_id):
    """
    Get all bot settings for an admin across all groups.
    Returns a list of settings objects, each representing a group's configuration.
    """
    try:
        query = """
            SELECT * FROM bot_settings
            WHERE admin_user_id = %s AND is_active = TRUE
            ORDER BY group_id
        """
        result = execute_query(query, (admin_user_id,), fetch=True)

        if not result:
            return []

        settings_list = []
        for row in result:
            settings = {
                'setting_id': row['setting_id'],
                'admin_user_id': row['admin_user_id'],
                'group_id': row['group_id'],
                'group_name': row['group_name'] if row['group_name'] else f"Group {row['group_id']}",  # Default name, can be customized later
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


def get_bot_settings_for_group(admin_user_id, group_id):
    """
    Get bot settings for a specific group.
    Returns the settings object for the group or None if not found.
    """
    try:
        query = """
            SELECT * FROM bot_settings
            WHERE admin_user_id = %s AND group_id = %s AND is_active = TRUE
        """
        result = execute_query(query, (admin_user_id, group_id), fetch=True)

        if not result:
            return None

        row = result[0]
        settings = {
            'setting_id': row['setting_id'],
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
    Returns True on success, False on failure.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Start transaction
                conn.start_transaction()

                # Prepare the data
                group_name = settings.get('group_name')
                license_key = settings.get('license_key')
                bot_username = settings.get('bot_username', 'BeHumanAgainBot')
                has_admin_permissions = settings.get('has_admin_permissions', False)
                event_type = settings.get('event_type', 'normal')
                event_name = settings.get('event_name', '')
                event_days = to_int_or_none(settings.get('event_days'))
                pass_points = to_int_or_none(settings.get('pass_points'))
                slots_per_day = to_int_or_none(settings.get('slots_per_day'))
                welcome_message = settings.get('welcome_message', '')
                kick_response = settings.get('kick_response', '')
                undesignated_slot_response = settings.get('undesignated_slot_response', '')
                leaderboard_time = to_str_or_none(settings.get('leaderboard_time'))
                banned_words = json.dumps(settings.get('banned_words', []))
                loaded_slots = json.dumps(settings.get('loaded_slots', []))

                # Insert or update bot settings for the event
                query = """
                    INSERT INTO bot_settings
                    (event_id, bot_username, has_admin_permissions, event_type, event_name, event_days, pass_points, slots_per_day,
                     welcome_message, kick_response, undesignated_slot_response, leaderboard_time, banned_words, loaded_slots, is_active)
                    VALUES (
                        (SELECT event_id FROM events WHERE license_key = %s),
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE
                    )
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
                    license_key, bot_username, has_admin_permissions, event_type, event_name, event_days, pass_points, slots_per_day,
                    welcome_message, kick_response, undesignated_slot_response, leaderboard_time, banned_words, loaded_slots
                )

                try:
                    cursor.execute(query, params)
                except Exception as e:
                    logger.error(f"Failed executing save_bot_settings. Query: {query} | Params: {params} | Error: {e}", exc_info=True)
                    raise

                # Commit transaction
                conn.commit()

                logger.info(f"Successfully saved bot settings for admin {admin_user_id}, group {group_id}")
                return True

    except Exception as e:
        logger.error(f"Error saving bot settings for group: {e}", exc_info=True)
        return False