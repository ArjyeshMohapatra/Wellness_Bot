from .utils import execute_query, get_db_connection, logger, ist, datetime, timedelta, json, save_base64_image, to_int_or_none, to_str_or_none


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
                from .banned_words import save_banned_words
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
        (admin_user_id, event_type, event_name, event_days, pass_points, slots_per_day,
         welcome_message, kick_response, undesignated_slot_response, leaderboard_time, max_members)
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
    try:
        cursor.execute(query, params)
    except Exception as e:
        logger.error(f"Failed executing save_or_update_admin_config. Query: {query} | Params: {params} | Error: {e}", exc_info=True)
        raise


def save_or_update_admin_slots(cursor, admin_user_id, slots_data):
    """Save or update admin slots"""
    # First, delete existing slots for this admin
    try:
        cursor.execute("DELETE FROM admin_slot_keywords WHERE slot_id IN (SELECT slot_id FROM admin_slots WHERE admin_user_id = %s)", (admin_user_id,))
    except Exception as e:
        logger.error(f"Failed executing save_or_update_admin_slots (delete keywords). Query: DELETE FROM admin_slot_keywords WHERE slot_id IN (SELECT slot_id FROM admin_slots WHERE admin_user_id = %s) | Params: {(admin_user_id,)} | Error: {e}", exc_info=True)
        raise
    try:
        cursor.execute("DELETE FROM admin_slots WHERE admin_user_id = %s", (admin_user_id,))
    except Exception as e:
        logger.error(f"Failed executing save_or_update_admin_slots (delete slots). Query: DELETE FROM admin_slots WHERE admin_user_id = %s | Params: {(admin_user_id,)} | Error: {e}", exc_info=True)
        raise

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
        try:
            cursor.execute(query, params)
        except Exception as e:
            logger.error(f"Failed executing save_or_update_admin_slots (insert slot). Query: {query} | Params: {params} | Error: {e}", exc_info=True)
            raise


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