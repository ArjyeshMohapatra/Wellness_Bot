from .utils import execute_query, get_db_connection, logger
from .member_management import get_member


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
            try:
                cursor.execute(query, (event_id, slot_id, user_id, username, first_name, last_name, status, points))
            except Exception as e:
                logger.error(f"Failed executing mark_slot_completed. Query: {query} | Params: {(event_id, slot_id, user_id, username, first_name, last_name, status, points)} | Error: {e}", exc_info=True)
                raise
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