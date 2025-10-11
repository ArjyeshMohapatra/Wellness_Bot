import os
import shutil
from pathlib import Path
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FileStorage:
    """Manages file storage for groups."""
    
    def __init__(self, base_path: str = "storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    async def save_photo(self, group_id: int, user_id: int, username: str, slot_name: str, file, filename: str) -> str:
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
    
    def get_group_path(self, group_id: str) -> Path:
        """Get the storage path for a specific group."""
        group_path = self.base_path / "groups" / str(group_id)
        group_path.mkdir(parents=True, exist_ok=True)
        return group_path
    
    def get_photos_path(self, group_id: str) -> Path:
        """Get the photos storage path for a specific group."""
        photos_path = self.get_group_path(group_id) / "photos"
        photos_path.mkdir(exist_ok=True)
        return photos_path
    
    def save_file(self, group_id: str, file_data: bytes, filename: str, subfolder: str = "") -> str:
        """Save a file to group storage."""
        try:
            if subfolder:
                save_path = self.get_group_path(group_id) / subfolder
                save_path.mkdir(exist_ok=True)
            else:
                save_path = self.get_group_path(group_id)
            
            file_path = save_path / filename
            
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"Saved file {filename} for group {group_id}")
            return str(file_path)
        
        except Exception as e:
            logger.error(f"Error saving file {filename} for group {group_id}: {e}")
            raise
    
    def delete_file(self, group_id: str, filename: str, subfolder: str = "") -> bool:
        """Delete a file from group storage."""
        try:
            if subfolder:
                file_path = self.get_group_path(group_id) / subfolder / filename
            else:
                file_path = self.get_group_path(group_id) / filename
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file {filename} for group {group_id}")
                return True
            return False
        
        except Exception as e:
            logger.error(f"Error deleting file {filename} for group {group_id}: {e}")
            return False
    
    def list_files(self, group_id: str, subfolder: str = "") -> list:
        """List all files in group storage."""
        try:
            if subfolder:
                list_path = self.get_group_path(group_id) / subfolder
            else:
                list_path = self.get_group_path(group_id)
            
            if not list_path.exists():
                return []
            
            files = [f.name for f in list_path.iterdir() if f.is_file()]
            return files
        
        except Exception as e:
            logger.error(f"Error listing files for group {group_id}: {e}")
            return []
    
    def cleanup_group_storage(self, group_id: str) -> bool:
        """Remove all storage for a group."""
        try:
            group_path = self.get_group_path(group_id)
            if group_path.exists():
                shutil.rmtree(group_path)
                logger.info(f"Cleaned up storage for group {group_id}")
                return True
            return False
        
        except Exception as e:
            logger.error(f"Error cleaning up storage for group {group_id}: {e}")
            return False