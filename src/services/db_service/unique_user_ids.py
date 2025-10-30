from .utils import execute_query, logger


def generate_unique_user_ids_for_group(group_id, count):
    """
    Generate unique user IDs for a group and store them in database.

    Args:
        group_id: The group ID for which to generate user IDs
        count: Number of user IDs to generate

    Returns:
        List of generated user IDs
    """
    from unique_user_id_generator import generate_user_ids_for_group
    return generate_user_ids_for_group(group_id, count)


def validate_unique_user_id(user_id):
    """
    Validate if a unique user ID exists and return group information.

    Args:
        user_id: The user ID to validate

    Returns:
        Dict with 'valid', 'group_id', and 'used' status
    """
    from unique_user_id_generator import validate_user_id
    return validate_user_id(user_id)


def assign_unique_user_id_to_member(group_id, user_id, unique_user_id):
    """
    Assign a unique user ID to a member (when they complete KYC).

    Args:
        group_id: The group ID
        user_id: The Telegram user ID
        unique_user_id: The unique user ID to assign

    Returns:
        Boolean indicating success
    """
    try:
        # First check if the unique user ID is available for this group
        validation = validate_unique_user_id(unique_user_id)
        if not validation['valid'] or validation['group_id'] != group_id or validation['used']:
            return False

        # Update the member record with the actual user_id
        query = """
            UPDATE group_members
            SET user_id = %s
            WHERE group_id = %s AND unique_user_id = %s AND user_id IS NULL
        """
        result = execute_query(query, (user_id, group_id, unique_user_id))

        return result > 0  # Returns True if at least one row was updated

    except Exception as e:
        logger.error(f"Error assigning unique user ID: {e}", exc_info=True)
        return False


def get_available_unique_user_ids(group_id):
    """
    Get all available (unused) unique user IDs for a group.

    Args:
        group_id: The group ID

    Returns:
        List of available unique user IDs
    """
    try:
        query = """
            SELECT unique_user_id
            FROM group_members
            WHERE group_id = %s AND unique_user_id IS NOT NULL AND user_id IS NULL
            ORDER BY unique_user_id
        """
        result = execute_query(query, (group_id,), fetch=True)
        return [row['unique_user_id'] for row in result] if result else []

    except Exception as e:
        logger.error(f"Error getting available unique user IDs: {e}", exc_info=True)
        return []