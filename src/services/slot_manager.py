import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SlotManager:
    """Manages time slots for group activities."""
    
    def __init__(self):
        self.slots: Dict[str, List[dict]] = {}
    
    def create_slot(self, group_id: str, slot_time: datetime, max_participants: int = 10) -> str:
        """Create a new time slot for a group."""
        slot_id = f"{group_id}_{slot_time.isoformat()}"
        
        if group_id not in self.slots:
            self.slots[group_id] = []
        
        slot = {
            'id': slot_id,
            'group_id': group_id,
            'time': slot_time,
            'max_participants': max_participants,
            'participants': [],
            'created_at': datetime.now()
        }
        
        self.slots[group_id].append(slot)
        logger.info(f"Created slot {slot_id} for group {group_id}")
        return slot_id
    
    def join_slot(self, slot_id: str, user_id: int, username: str) -> bool:
        """Add a user to a time slot."""
        for group_id, group_slots in self.slots.items():
            for slot in group_slots:
                if slot['id'] == slot_id:
                    if len(slot['participants']) < slot['max_participants']:
                        if user_id not in [p['user_id'] for p in slot['participants']]:
                            slot['participants'].append({
                                'user_id': user_id,
                                'username': username,
                                'joined_at': datetime.now()
                            })
                            logger.info(f"User {user_id} joined slot {slot_id}")
                            return True
        return False
    
    def leave_slot(self, slot_id: str, user_id: int) -> bool:
        """Remove a user from a time slot."""
        for group_id, group_slots in self.slots.items():
            for slot in group_slots:
                if slot['id'] == slot_id:
                    slot['participants'] = [p for p in slot['participants'] if p['user_id'] != user_id]
                    logger.info(f"User {user_id} left slot {slot_id}")
                    return True
        return False
    
    def get_group_slots(self, group_id: str) -> List[dict]:
        """Get all slots for a group."""
        return self.slots.get(group_id, [])
    
    def cleanup_old_slots(self, hours_old: int = 24):
        """Remove slots older than specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        
        for group_id in self.slots:
            self.slots[group_id] = [
                slot for slot in self.slots[group_id] 
                if slot['time'] > cutoff_time
            ]