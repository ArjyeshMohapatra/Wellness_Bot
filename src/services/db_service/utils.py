import logging
from datetime import datetime, timedelta
from pytz import timezone
try:
    from ...config import NEW_MEMBER_RESTRICTION_MINUTES
    from ...db import execute_query, get_db_connection
except ImportError:
    from config import NEW_MEMBER_RESTRICTION_MINUTES
    from db import execute_query, get_db_connection
import mysql.connector
import json
import base64
import os
from pathlib import Path

ist = timezone("Asia/Kolkata")
logger = logging.getLogger(__name__)


def save_base64_image(base64_data, admin_user_id, slot_name):
    """Save a Base64 encoded image and return the file path."""
    try:
        if not base64_data or not base64_data.startswith('data:image/'):
            return base64_data  # Return as-is if not Base64

        # Extract the Base64 data (remove the data:image/... prefix)
        header, encoded = base64_data.split(',', 1)
        image_data = base64.b64decode(encoded)

        # Determine file extension from header
        if 'jpeg' in header or 'jpg' in header:
            ext = 'jpg'
        elif 'png' in header:
            ext = 'png'
        elif 'gif' in header:
            ext = 'gif'
        elif 'webp' in header:
            ext = 'webp'
        else:
            ext = 'jpg'  # Default

        # Create directory structure
        storage_path = Path('storage/admin_images')
        storage_path.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"admin_{admin_user_id}_{slot_name}_{timestamp}.{ext}"
        file_path = storage_path / filename

        # Save the image
        with open(file_path, 'wb') as f:
            f.write(image_data)

        # Return relative path for storage
        return str(file_path)

    except Exception as e:
        logger.error(f"Error saving Base64 image: {e}")
        return base64_data  # Return original data on error


# Helper function to convert empty strings to None for integer fields
def to_int_or_none(value):
    if value == '' or value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def to_str_or_none(value):
    if value == "" or value is None:
        return None
    return str(value)