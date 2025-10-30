from .utils import execute_query, get_db_connection, logger, ist, datetime, timedelta, NEW_MEMBER_RESTRICTION_MINUTES
from .group_config import get_restriction_until_time
from .subscription_limits import can_admin_add_member
import mysql.connector


# gets info regarding members who joins back group
def get_returning_member_info(group_id, user_id):
    """
    Checks if a user is in the history.
    Returns their most recent record (as a dict) if found, otherwise None.
    """
    # gets most recent history about an user
    query = """
    SELECT * FROM member_history WHERE group_id = %s AND user_id = %s ORDER BY action_at DESC LIMIT 1
    """
    result = execute_query(query, (group_id, user_id), fetch=True)
    return result[0] if result else None  # Returns all columns or None


def add_member(group_id, user_id, username=None, first_name=None, last_name=None, is_admin=False, restrict_new=True):
    """
    Atomically adds or updates a member using INSERT ... ON DUPLICATE KEY UPDATE.
    Returns the member's data and a boolean indicating if they were newly inserted.
    Now checks subscription limits for new members.
    """
    try:
        # checks if the member exists to determine if this is a new join
        existing = get_member(group_id, user_id)
        is_new = existing is None

        # For new members, check subscription limits
        if is_new and not is_admin:
            # Get admin for this group
            admin_query = """
                SELECT l.assigned_admin_id
                FROM groups_config gc
                JOIN licenses l ON gc.license_key = l.license_key
                WHERE gc.group_id = %s
            """
            admin_result = execute_query(admin_query, (group_id,), fetch=True)
            if admin_result:
                admin_user_id = admin_result[0]['assigned_admin_id']
                if not can_admin_add_member(admin_user_id):
                    logger.warning(f"Cannot add member {user_id} to group {group_id}: subscription limit reached for admin {admin_user_id}")
                    return None, False  # Return None to indicate failure

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
                    user_day_number = 1  # resets day number for user to 1 if reset happens
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
                try:
                    cursor.execute(query_1, (
                        user_id, group_id, username, first_name, last_name, 1 if is_admin else 0,
                        is_restricted, restriction_until, cycle_start_date, cycle_end_date,
                        total_points, knockout_points, general_warnings, banned_word_count, user_day_number
                    ))
                except Exception as e:
                    logger.error(f"Failed executing add_member (insert/update). Query: {query_1} | Params: {(user_id, group_id, username, first_name, last_name, 1 if is_admin else 0, is_restricted, restriction_until, cycle_start_date, cycle_end_date, total_points, knockout_points, general_warnings, banned_word_count, user_day_number)} | Error: {e}", exc_info=True)
                    raise

                # If member is new, also log to member_history table
                if is_new:
                    try:
                        cursor.execute(query_2, (
                            group_id, user_id, username, first_name, last_name,
                            total_points, knockout_points, general_warnings, banned_word_count,
                            user_day_number, cycle_start_date, cycle_end_date
                        ))
                    except Exception as e:
                        logger.error(f"Failed executing add_member (history insert). Query: {query_2} | Params: {(group_id, user_id, username, first_name, last_name, total_points, knockout_points, general_warnings, banned_word_count, user_day_number, cycle_start_date, cycle_end_date)} | Error: {e}", exc_info=True)
                        raise
                    logger.debug(f"[DEBUG] Complete 'joined' record created for new user {user_id}")
        member_data = get_member(group_id, user_id)
        return member_data, is_new

    except mysql.connector.Error as e:
        logger.error("DATABASE ERROR during transaction in add_member for user %s: %s", user_id, e, exc_info=True)
        return None, False

    except Exception as e:
        logger.error("UNEXPECTED ERROR in add_member for user %s: %s", user_id, e, exc_info=True)
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
        logger.error(f"Error deducting knockout points: {e}", exc_info=True)
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
                try:
                    cursor.execute(archive_query, (
                    member['group_id'], member['user_id'], member.get('username'), member.get('first_name'), member.get('last_name'),
                    member.get('total_points'), member.get('knockout_points'), member.get('general_warnings'), member.get('banned_word_count'),
                    member.get('user_day_number'), member.get('cycle_start_date'), member.get('cycle_end_date'), member.get('is_restricted', 0),
                    member.get('joined_at'), member.get('last_active_timestamp'), action
                    ))
                except Exception as e:
                    logger.error(f"Failed executing remove_member (archive). Query: {archive_query} | Params: {(member['group_id'], member['user_id'], member.get('username'), member.get('first_name'), member.get('last_name'), member.get('total_points'), member.get('knockout_points'), member.get('general_warnings'), member.get('banned_word_count'), member.get('user_day_number'), member.get('cycle_start_date'), member.get('cycle_end_date'), member.get('is_restricted', 0), member.get('joined_at'), member.get('last_active_timestamp'), action)} | Error: {e}", exc_info=True)
                    raise

                # Finally, delete the member from the main table
                try:
                    cursor.execute("DELETE FROM group_members WHERE group_id = %s AND user_id = %s", (group_id, user_id))
                except Exception as e:
                    logger.error(f"Failed executing remove_member (delete). Query: DELETE FROM group_members WHERE group_id = %s AND user_id = %s | Params: {(group_id, user_id)} | Error: {e}", exc_info=True)
                    raise
                conn.commit()  # Ensure both operations are committed together
        logger.info(f"Archived and removed member {user_id} from group {group_id}.")
        return True
    except Exception as e:
        logger.error(f"Error removing member {user_id}: {e}", exc_info=True)
        return False


def get_group_max_members(group_id):
    """
    Get the maximum number of members allowed for a group.

    Args:
        group_id: The group ID

    Returns:
        Maximum number of members (int)
    """
    try:
        query = "SELECT max_members FROM groups_config WHERE group_id = %s"
        result = execute_query(query, (group_id,), fetch=True)
        return result[0]['max_members'] if result else 100  # Default to 100

    except Exception as e:
        logger.error(f"Error getting group max members: {e}", exc_info=True)
        return 100