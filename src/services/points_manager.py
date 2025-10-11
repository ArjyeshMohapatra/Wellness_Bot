from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PointsManager:
    """Manages user points and rewards system."""
    
    def __init__(self):
        self.user_points: Dict[str, Dict[int, int]] = {}  # group_id -> user_id -> points
    
    def add_points(self, group_id: str, user_id: int, points: int, reason: str = "") -> int:
        """Add points to a user in a specific group."""
        if group_id not in self.user_points:
            self.user_points[group_id] = {}
        
        if user_id not in self.user_points[group_id]:
            self.user_points[group_id][user_id] = 0
        
        self.user_points[group_id][user_id] += points
        
        logger.info(f"Added {points} points to user {user_id} in group {group_id}. Reason: {reason}")
        return self.user_points[group_id][user_id]
    
    def remove_points(self, group_id: str, user_id: int, points: int, reason: str = "") -> int:
        """Remove points from a user in a specific group."""
        if group_id not in self.user_points:
            self.user_points[group_id] = {}
        
        if user_id not in self.user_points[group_id]:
            self.user_points[group_id][user_id] = 0
        
        self.user_points[group_id][user_id] = max(0, self.user_points[group_id][user_id] - points)
        
        logger.info(f"Removed {points} points from user {user_id} in group {group_id}. Reason: {reason}")
        return self.user_points[group_id][user_id]
    
    def get_points(self, group_id: str, user_id: int) -> int:
        """Get points for a user in a specific group."""
        if group_id not in self.user_points:
            return 0
        return self.user_points[group_id].get(user_id, 0)
    
    def get_leaderboard(self, group_id: str, limit: int = 10) -> list:
        """Get top users by points in a group."""
        if group_id not in self.user_points:
            return []
        
        sorted_users = sorted(
            self.user_points[group_id].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_users[:limit]
    
    def reset_user_points(self, group_id: str, user_id: int) -> bool:
        """Reset points for a specific user in a group."""
        if group_id in self.user_points and user_id in self.user_points[group_id]:
            self.user_points[group_id][user_id] = 0
            logger.info(f"Reset points for user {user_id} in group {group_id}")
            return True
        return False
    
    def reset_group_points(self, group_id: str) -> bool:
        """Reset all points in a group."""
        if group_id in self.user_points:
            self.user_points[group_id].clear()
            logger.info(f"Reset all points in group {group_id}")
            return True
        return False