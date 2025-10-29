import logging
import random
import string
from src.db import execute_query

logger = logging.getLogger(__name__)


def generate_user_ids_for_group(group_id, count):
    """
    Generate unique user IDs for a group and store them in database.

    Args:
        group_id: The group ID for which to generate user IDs
        count: Number of user IDs to generate

    Returns:
        List of generated user IDs
    """
    try:
        generated_ids = []
        attempts = 0
        max_attempts = count * 10  # Prevent infinite loops

        while len(generated_ids) < count and attempts < max_attempts:
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

        if len(generated_ids) < count:
            logger.error(f"Could only generate {len(generated_ids)} out of {count} user IDs for group {group_id}")
        else:
            logger.info(f"Successfully generated {count} unique user IDs for group {group_id}")

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