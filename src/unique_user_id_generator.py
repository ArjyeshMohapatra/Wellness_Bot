import random
import string
from typing import List, Set
from .db import execute_query

class UniqueUserIDGenerator:
    """Generator for unique user IDs similar to Telegram user IDs"""

    def __init__(self):
        self.used_ids = set()
        self._load_existing_ids()

    def _load_existing_ids(self):
        """Load existing unique user IDs from database"""
        try:
            query = "SELECT unique_user_id FROM group_members WHERE unique_user_id IS NOT NULL"
            result = execute_query(query, fetch=True)
            if result:
                self.used_ids = {row['unique_user_id'] for row in result}
        except Exception as e:
            print(f"Warning: Could not load existing IDs: {e}")
            self.used_ids = set()

    def generate_unique_id(self) -> str:
        """Generate a single unique 6-digit user ID"""
        while True:
            # Generate a 6-digit number (similar to Telegram user IDs)
            user_id = str(random.randint(100000, 999999))

            if user_id not in self.used_ids:
                self.used_ids.add(user_id)
                return user_id

    def generate_multiple_ids(self, count: int) -> List[str]:
        """Generate multiple unique user IDs"""
        ids = []
        for _ in range(count):
            ids.append(self.generate_unique_id())
        return ids

    def is_id_available(self, user_id: str) -> bool:
        """Check if a user ID is available"""
        return user_id not in self.used_ids

    def mark_id_as_used(self, user_id: str):
        """Mark a user ID as used"""
        self.used_ids.add(user_id)

def generate_user_ids_for_group(group_id: int, count: int) -> List[str]:
    """
    Generate unique user IDs for a specific group and store them in database

    Args:
        group_id: The group ID for which to generate user IDs
        count: Number of user IDs to generate

    Returns:
        List of generated user IDs
    """
    generator = UniqueUserIDGenerator()
    user_ids = generator.generate_multiple_ids(count)

    # Store the generated IDs in database with the group_id
    for user_id in user_ids:
        try:
            query = """
                INSERT INTO group_members (user_id, group_id, unique_user_id, joined_at)
                VALUES (0, %s, %s, NOW())
            """
            execute_query(query, (group_id, user_id))
        except Exception as e:
            print(f"Error storing user ID {user_id}: {e}")
            continue

    return user_ids

def validate_user_id(user_id: str) -> dict:
    """
    Validate if a user ID exists and return group information

    Args:
        user_id: The user ID to validate

    Returns:
        Dict with 'valid', 'group_id', and 'used' status
    """
    try:
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
                'used': row['user_id'] != 0  # If user_id is 0, it's not used yet
            }
        else:
            return {'valid': False, 'group_id': None, 'used': False}
    except Exception as e:
        print(f"Error validating user ID: {e}")
        return {'valid': False, 'group_id': None, 'used': False}

if __name__ == "__main__":
    # Test the generator
    generator = UniqueUserIDGenerator()
    test_ids = generator.generate_multiple_ids(5)
    print(f"Generated test IDs: {test_ids}")

    # Test validation
    for test_id in test_ids[:2]:  # Test first 2 IDs
        validation = validate_user_id(test_id)
        print(f"ID {test_id} validation: {validation}")