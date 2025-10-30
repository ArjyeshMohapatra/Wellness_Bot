import logging
import random
import string
from src.db import execute_query

logger = logging.getLogger(__name__)


def generate_user_ids_for_group(group_id, count):
    """
    Generate unique user IDs for a group and store them in database.
    Now checks subscription limits across all groups for the admin.

    Args:
        group_id: The group ID for which to generate user IDs
        count: Number of user IDs to generate

    Returns:
        List of generated user IDs
    """
    try:
        # First, get the admin for this group
        admin_query = """
            SELECT l.assigned_admin_id
            FROM groups_config gc
            JOIN licenses l ON gc.license_key = l.license_key
            WHERE gc.group_id = %s
        """
        admin_result = execute_query(admin_query, (group_id,), fetch=True)
        if not admin_result:
            logger.error(f"No admin found for group {group_id}")
            return []

        admin_user_id = admin_result[0]['assigned_admin_id']

        # Check current subscription limits
        from src.services.database_service import get_admin_subscription_limits
        limits = get_admin_subscription_limits(admin_user_id)
        if not limits:
            logger.error(f"No subscription limits found for admin {admin_user_id}")
            return []

        # Count current total members across all groups for this admin
        current_total_query = """
            SELECT COUNT(*) as total
            FROM group_members gm
            JOIN groups_config gc ON gm.group_id = gc.group_id
            JOIN licenses l ON gc.license_key = l.license_key
            WHERE l.assigned_admin_id = %s AND gm.unique_user_id IS NOT NULL
        """
        current_total_result = execute_query(current_total_query, (admin_user_id,), fetch=True)
        current_total = current_total_result[0]['total'] if current_total_result else 0

        # Check if we can generate the requested count
        available_slots = limits['max_members'] - current_total
        if available_slots <= 0:
            logger.warning(f"Admin {admin_user_id} has reached subscription limit. Current: {current_total}, Max: {limits['max_members']}")
            return []

        actual_count = min(count, available_slots)

        generated_ids = []
        attempts = 0
        max_attempts = actual_count * 10  # Prevent infinite loops

        while len(generated_ids) < actual_count and attempts < max_attempts:
            # Generate a 6-digit random number
            user_id = ''.join(random.choices(string.digits, k=6))

            # Check if this ID already exists
            query = "SELECT member_id FROM group_members WHERE unique_user_id = %s"
            result = execute_query(query, (user_id,), fetch=True)

            if not result:
                # ID is available, insert it
                query = """
                    INSERT INTO group_members (group_id, unique_user_id)
                    VALUES (%s, %s)
                """
                execute_query(query, (group_id, user_id))
                generated_ids.append(user_id)
                logger.info(f"Generated unique user ID {user_id} for group {group_id}")

            attempts += 1

        if len(generated_ids) < actual_count:
            logger.error(f"Could only generate {len(generated_ids)} out of {actual_count} user IDs for group {group_id}")
        else:
            logger.info(f"Successfully generated {actual_count} unique user IDs for group {group_id}")

        return generated_ids

    except Exception as e:
        logger.error(f"Error generating user IDs for group {group_id}: {e}", exc_info=True)
        return []


def validate_user_id(user_id):
    """
    Validate if a unique user ID exists and return group information.

    Args:
        user_id: The user ID to validate (string)

    Returns:
        Dict with 'valid' (bool), 'group_id' (int or None), 'used' (bool) keys
    """
    try:
        # Check if the user ID exists in group_members
        query = """
            SELECT group_id, user_id
            FROM group_members
            WHERE unique_user_id = %s
        """
        result = execute_query(query, (user_id,), fetch=True)

        if result and len(result) > 0:
            row = result[0]
            return {
                'valid': True,
                'group_id': row['group_id'],
                'used': row['user_id'] is not None  # If user_id is set, it's been assigned
            }
        else:
            return {
                'valid': False,
                'group_id': None,
                'used': False
            }

    except Exception as e:
        logger.error(f"Error validating user ID {user_id}: {e}", exc_info=True)
        return {
            'valid': False,
            'group_id': None,
            'used': False
        }