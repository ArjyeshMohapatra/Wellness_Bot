from .utils import execute_query, get_db_connection, logger, ist, datetime, timedelta, json, NEW_MEMBER_RESTRICTION_MINUTES
from .events_slots import get_all_slots


def get_group_config(group_id):
    query = "SELECT * FROM groups_config WHERE group_id = %s"
    result = execute_query(query, (group_id,), fetch=True)
    return result[0] if result else None


def get_active_group_id():
    """Get the active group ID (the one with a license key)."""
    query = "SELECT group_id FROM groups_config WHERE event_id IS NOT NULL AND group_id != 0 LIMIT 1"
    result = execute_query(query, fetch=True)
    return result[0]["group_id"] if result else None


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
        logger.error(f"Error creating group config: {e}", exc_info=True)
        return False


def create_pending_group_config(group_id, admin_user_id):
    try:
        # Check if group config already exists
        existing_config = get_group_config(group_id)

        if not existing_config:
            execute_query(
                """
                    INSERT INTO groups_config
                    (group_id, admin_user_id, max_members, welcome_message, kick_message)
                    VALUES (%s, %s, 100, 'Welcome! Hoping that you will enjoy your time in here. 🌟', 'Goodbye, hope you enjoyed your time while being with us!')
                """,
                (group_id, admin_user_id),
            )

            logger.info(f"Created pending group config for {group_id} (waiting for license)")

        # Always try to create event and slots (will check if they exist)
        create_default_event_and_slots(group_id)

        return True
    except Exception as e:
        logger.error(f"Error creating pending group config: {e}", exc_info=True)
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
                "Is this your breakfast ?",
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
        logger.error(f"Error creating default slots: {e}", exc_info=True)
        return False


def update_group_config(cursor, group_id, admin_user_id, config_data):
    """Update group configuration in groups_config table"""
    # Coerce and sanitize incoming config data to avoid passing unexpected types to SQL params
    try:
        welcome_message = str(config_data.get('welcome_message', '') or '')
    except Exception:
        welcome_message = ''
    try:
        kick_message = str(config_data.get('kick_response', '') or '')
    except Exception:
        kick_message = ''
    try:
        max_members = int(config_data.get('max_members')) if config_data.get('max_members') not in (None, '') else 0
    except Exception:
        max_members = 0
    try:
        undesignated_slot_response = str(config_data.get('undesignated_slot_response', '') or '')
    except Exception:
        undesignated_slot_response = ''
    leaderboard_time_val = config_data.get('leaderboard_time', None)
    leaderboard_time = leaderboard_time_val if leaderboard_time_val not in ('', None) else None

    if group_id is None:
        # For admin templates, check if config already exists for this admin
        try:
            cursor.execute("SELECT config_id FROM groups_config WHERE group_id IS NULL AND admin_user_id = %s", (admin_user_id,))
        except Exception as e:
            logger.error(f"Failed executing update_group_config (select admin template). Query: SELECT config_id FROM groups_config WHERE group_id IS NULL AND admin_user_id = %s | Params: {(admin_user_id,)} | Error: {e}", exc_info=True)
            raise
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
                welcome_message,
                kick_message,
                max_members,
                undesignated_slot_response,
                leaderboard_time,
                existing[0]  # config_id
            )
            try:
                cursor.execute(query, params)
            except Exception as e:
                logger.error(f"Failed executing update_group_config (admin template update). Query: {query} | Params: {params} | Error: {e}", exc_info=True)
                raise
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
                welcome_message,
                kick_message,
                max_members,
                undesignated_slot_response,
                leaderboard_time
            )
            try:
                cursor.execute(query, params)
            except Exception as e:
                logger.error(f"Failed executing update_group_config (admin template insert). Query: {query} | Params: {params} | Error: {e}", exc_info=True)
                raise
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
            welcome_message,
            kick_message,
            max_members,
            undesignated_slot_response,
            leaderboard_time
        )
        try:
            cursor.execute(query, params)
        except Exception as e:
            logger.error(f"Failed executing update_group_config (group insert/update). Query: {query} | Params: {params} | Error: {e}", exc_info=True)
            raise


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
        from .events_slots import get_active_event
        event = get_active_event(group_id)

        # Get slots
        from .events_slots import get_all_slots
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


def create_group_config_detailed(group_id, admin_user_id):
    """Create initial group configuration when bot joins a group (detailed version from admin_panel)"""
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
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(slot_query, (group_id, admin_user_id, event_id, slot_name, start_time, end_time, initial_msg, positive_msg, '', 0, True, 'media'))

                # Commit transaction
                connection.commit()
                logger.info(f"Created default configuration for group {group_id}")
                return True

            except Exception as e:
                connection.rollback()
                logger.error(f"Error creating group config: {e}")
                raise

    except Exception as e:
        logger.error(f"Error in create_group_config_detailed: {e}")
        return False