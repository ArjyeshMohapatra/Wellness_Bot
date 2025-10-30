from .utils import execute_query, logger


def get_admin_subscription_limits(admin_user_id):
    """Get subscription limits for an admin."""
    try:
        query = "SELECT * FROM admin_subscription_limits WHERE admin_user_id = %s"
        result = execute_query(query, (admin_user_id,), fetch=True)
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting subscription limits: {e}")
        return None


def can_admin_add_member(admin_user_id):
    """Check if admin can add more members based on subscription limits."""
    try:
        limits = get_admin_subscription_limits(admin_user_id)
        if not limits:
            return False
        return limits['current_total_members'] < limits['max_members']
    except Exception as e:
        logger.error(f"Error checking member addition permission: {e}")
        return False