from .utils import execute_query, get_db_connection, logger
from .member_management import deduct_knockout_points


def penalize_zero_activity_members(group_id, event_id, points_to_deduct):
    """Finds members with no slot completions for today and deducts knockout points."""
    try:
        query_1 = """
            SELECT DISTINCT user_id
            FROM daily_slot_tracker
            WHERE event_id = %s AND log_date = CURDATE() AND status = 'completed'
        """
        active_members_result = execute_query(query_1, (event_id,), fetch=True)
        active_user_ids = {row["user_id"] for row in active_members_result}

        # Get all non-restricted members in the group.
        query_2 = """
            SELECT user_id, first_name
            FROM group_members
            WHERE group_id = %s AND is_restricted = 0
        """
        all_members = execute_query(query_2, (group_id,), fetch=True)

        inactive_members = []
        for member in all_members:
            if member["user_id"] not in active_user_ids:
                inactive_members.append(member)

        # Apply a penalty to each inactive member.
        for member in inactive_members:
            user_id = member["user_id"]
            first_name = member.get("first_name", f"User_{user_id}")
            deduct_knockout_points(group_id, user_id, points_to_deduct)
            logger.info(
                f"Penalized {first_name} ({user_id}) with {points_to_deduct} knockout points for zero activity today."
            )
        return inactive_members
    except Exception as e:
        logger.error(f"Error in penalize_zero_activity_members: {e}", exc_info=True)
        return []


def set_runtime_state(group_id, key, value):
    """Sets or updates a runtime state variable for a group."""
    query = """
    INSERT INTO runtime_state (group_id,state_key,state_value) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE state_value=VALUES(state_value)
    """
    execute_query(query, (group_id, key, str(value) if value is not None else None))


def get_runtime_state(group_id, key):
    """Gets a runtime state variable for a group."""
    query = """
    SELECT state_value FROM runtime_state WHERE group_id = %s AND state_key = %s
    """
    result = execute_query(query, (group_id, key), fetch=True)
    return result[0]["state_value"] if result else None


def update_admin_status(group_id, admin_user_ids):
    """
    Synchronizes the admin status for all members in a group within a single transaction.
    Sets is_admin = 1 for users in the admin_user_ids list and 0 for all others.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query_1 = """
                UPDATE group_members SET is_admin = 0 WHERE group_id = %s
                """
                try:
                    cursor.execute(query_1, (group_id,))
                except Exception as e:
                    logger.error(f"Failed executing update_admin_status (reset admins). Query: {query_1} | Params: {(group_id,)} | Error: {e}", exc_info=True)
                    raise

                if admin_user_ids:
                    placeholders = ', '.join(['%s'] * len(admin_user_ids))
                    query_2 = f"UPDATE group_members SET is_admin = 1 WHERE group_id = %s AND user_id IN ({placeholders})"
                    params = (group_id,) + tuple(admin_user_ids)
                    try:
                        cursor.execute(query_2, params)
                    except Exception as e:
                        logger.error(f"Failed executing update_admin_status (set admins). Query: {query_2} | Params: {params} | Error: {e}", exc_info=True)
                        raise
                conn.commit()
        logger.info(f"Successfully synchronized admin status for group {group_id}.")
        return True
    except Exception as e:
        logger.error(f"Failed to synchronize admin status for group {group_id}: {e}", exc_info=True)
        return False