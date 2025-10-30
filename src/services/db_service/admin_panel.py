from .utils import get_db_connection, logger
from .group_config import update_group_config
from .events_slots import save_or_update_event, save_or_update_slots
from .banned_words import save_banned_words


def save_admin_panel_config(admin_user_id, group_id, config_data):
    """Save admin panel configuration"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Start transaction
            connection.start_transaction()

            try:
                # Save group configuration
                update_group_config(cursor, group_id, admin_user_id, config_data)

                # Only save events and slots if we have a specific group_id
                # (not for admin templates where group_id is None)
                if group_id is not None:
                    # Save event and slots
                    event_id = save_or_update_event(cursor, group_id, config_data)
                    save_or_update_slots(cursor, group_id, admin_user_id, event_id, config_data.get('slots', []))

                # Save banned words (always global for now)
                banned_words = config_data.get('banned_words', [])
                if banned_words:
                    save_banned_words(cursor, group_id, banned_words)

                # Commit transaction
                connection.commit()
                logger.info(f"Saved admin panel config for admin {admin_user_id}, group {group_id}")

                return True

            except Exception as e:
                connection.rollback()
                logger.error(f"Error saving admin panel config: {e}")
                raise

    except Exception as e:
        logger.error(f"Error in save_admin_panel_config: {e}")
        return False

