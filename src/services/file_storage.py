from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FileStorage:
    """Manages file storage for groups."""
    
    def __init__(self, base_path: str = "storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    async def save_photo(self, group_id, user_id, username, slot_name, file, filename):
        """Save a photo from Telegram to local storage."""
        try:
            today_date = datetime.now().strftime("%Y_%m_%d")
            post_time = datetime.now().strftime("%Y_%m_%d_%I_%M_%S_%p").lower()
            
            photos_path = (self.base_path / "groups" / f"gid_{group_id}" / "photos" / today_date / slot_name)
            photos_path.mkdir(parents=True, exist_ok=True)
            
            file_path = photos_path / filename
            
            # Download file from Telegram
            await file.download_to_drive(str(file_path))
            
            logger.info(f"Saved photo for user {user_id} in group {group_id}: {filename}")
            return str(file_path)
        
        except Exception as e:
            logger.error(f"Error saving photo: {e}")
            raise