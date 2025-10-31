from .utils import execute_query, get_db_connection, logger, ist, datetime, timedelta, json, save_base64_image


def get_active_event(group_id):
    query = """
            SELECT e.* FROM events e
            JOIN groups_config gc ON e.event_id = gc.event_id
            WHERE gc.group_id = %s AND e.is_active = TRUE
            AND CURDATE() BETWEEN e.start_date AND e.end_date
            LIMIT 1
        """
    result = execute_query(query, (group_id,), fetch=True)
    return result[0] if result else None


def get_active_slot(group_id):
    query = """
            SELECT es.* FROM event_slots es
            JOIN groups_config gc ON es.event_id = gc.event_id
            WHERE gc.group_id = %s
            AND (
                (es.start_time <= es.end_time AND CURTIME() BETWEEN es.start_time AND es.end_time)
                OR
                (es.start_time > es.end_time AND (CURTIME() >= es.start_time OR CURTIME() <= es.end_time))
            )
            LIMIT 1
        """
    result = execute_query(query, (group_id,), fetch=True)
    return result[0] if result else None


def get_all_slots(group_id):
    query = """
        SELECT es.* FROM event_slots es
        JOIN groups_config gc ON es.event_id = gc.event_id
        WHERE gc.group_id = %s
        ORDER BY es.start_time
    """
    return execute_query(query, (group_id,), fetch=True)


def get_slot_keywords(slot_id):
    query = "SELECT keyword FROM slot_keywords WHERE slot_id = %s"
    results = execute_query(query, (slot_id,), fetch=True)
    return [r["keyword"] for r in results] if results else []


def log_missed_slots(group_id, event_id, slot_id):
    """
    Finds all non-restricted members who did not complete a slot
    and marks it as 'missed' in the daily_slot_tracker.
    """
    try:
        get_query = """
        SELECT user_id, username, first_name, last_name FROM group_members WHERE group_id = %s AND is_restricted = 0
        """
        non_restricted_members = execute_query(get_query, (group_id,), fetch=True)
        if not non_restricted_members:
            return  # no active members to log
        completed_query = """
        SELECT DISTINCT user_id FROM daily_slot_tracker WHERE event_id = %s AND slot_id = %s AND log_date = CURDATE()
        """
        completed_result = execute_query(completed_query, (event_id, slot_id), fetch=True)
        completed_user_ids = {row['user_id'] for row in completed_result}

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
            insert_query = """
            INSERT IGNORE INTO daily_slot_tracker (
                event_id, slot_id, user_id, username, first_name, last_name,
                log_date, status, points_scored) VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s, 0)
            """
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    try:
                        cursor.executemany(insert_query, missed_members_data)
                    except Exception as e:
                        logger.error(f"Failed executing log_missed_slots executemany. Query: {insert_query} | Params: {missed_members_data} | Error: {e}", exc_info=True)
                        raise

            logger.info(f"Logged {len(missed_members_data)} 'missed' entries for slot {slot_id} in group {group_id}", exc_info=True)
    except Exception as e:
        logger.error(f"Error in log_missed_slots_for_group: {e}", exc_info=True)


def save_or_update_event(cursor, group_id, config_data):
    """Save or update event configuration"""
    event_name = config_data.get('event_name', 'Wellness Challenge')
    event_type = config_data.get('event_type', 'normal')
    event_days = int(config_data.get('event_days') or 7)
    pass_points = int(config_data.get('pass_points') or 250)

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
    try:
        cursor.execute("SELECT event_id FROM events WHERE group_id = %s", (group_id,))
    except Exception as e:
        logger.error(f"Failed executing save_or_update_event (select existing). Query: SELECT event_id FROM events WHERE group_id = %s | Params: {(group_id,)} | Error: {e}", exc_info=True)
        raise
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
        try:
            cursor.execute(query, params)
        except Exception as e:
            logger.error(f"Failed executing save_or_update_event (update existing). Query: {query} | Params: {params} | Error: {e}", exc_info=True)
            raise
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
        try:
            cursor.execute(query, params)
        except Exception as e:
            logger.error(f"Failed executing save_or_update_event (insert new). Query: {query} | Params: {params} | Error: {e}", exc_info=True)
            raise
        return cursor.lastrowid


def save_or_update_slots(cursor, group_id, admin_user_id, event_id, slots_data):
    """Save or update slot configurations for an event"""
    # First, get existing slots for this event
    try:
        cursor.execute("SELECT slot_id, slot_name FROM event_slots WHERE event_id = %s", (event_id,))
    except Exception as e:
        logger.error(f"Failed executing save_or_update_slots (select event slots). Query: SELECT slot_id, slot_name FROM event_slots WHERE event_id = %s | Params: {(event_id,)} | Error: {e}", exc_info=True)
        raise
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
        try:
            cursor.execute("DELETE FROM event_slots WHERE slot_id = %s", (existing_slots[slot_name],))
        except Exception as e:
            logger.error(f"Failed executing save_or_update_slots (delete slot). Query: DELETE FROM event_slots WHERE slot_id = %s | Params: {(existing_slots[slot_name],)} | Error: {e}", exc_info=True)
            raise


def create_slot(cursor, slot_config):
    """Create a new slot"""
    query = """
        INSERT INTO event_slots (
            event_id, slot_name, start_time, end_time, initial_message,
            response_positive, response_clarify, image_file_path, slot_points, is_mandatory, slot_type,
            button_count, button_names, button_values
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        slot_config['event_id'], slot_config['slot_name'],
        slot_config['start_time'], slot_config['end_time'], slot_config['initial_message'],
        slot_config['response_positive'], '',  # response_clarify is empty for now
        slot_config['image_file_path'], slot_config['slot_points'], slot_config['is_mandatory'],
        slot_config['slot_type'], slot_config['button_count'], slot_config['button_names'], slot_config['button_values']
    )
    try:
        cursor.execute(query, params)
    except Exception as e:
        logger.error(f"Failed executing create_slot. Query: {query} | Params: {params} | Error: {e}", exc_info=True)
        raise


def update_slot(cursor, slot_id, slot_config):
    """Update an existing slot"""
    query = """
        UPDATE event_slots SET
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
    try:
        cursor.execute(query, params)
    except Exception as e:
        logger.error(f"Failed executing update_slot. Query: {query} | Params: {params} | Error: {e}", exc_info=True)
        raise