from datetime import datetime, time, timedelta
from typing import Optional, Tuple
import pytz

def parse_time_string(time_str: str) -> Optional[time]:
    """Parse time string in various formats (HH:MM, H:MM, etc.)."""
    try:
        # Handle different time formats
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                hour = int(parts[0])
                minute = int(parts[1])
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return time(hour, minute)
        else:
            # Handle hour only
            hour = int(time_str)
            if 0 <= hour <= 23:
                return time(hour, 0)
    except ValueError:
        pass
    return None

def combine_date_time(date_obj: datetime.date, time_obj: time, timezone_str: str = 'UTC') -> datetime:
    """Combine date and time objects with timezone."""
    tz = pytz.timezone(timezone_str)
    dt = datetime.combine(date_obj, time_obj)
    return tz.localize(dt)

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime to string."""
    return dt.strftime(format_str)

def get_time_until(target_datetime: datetime) -> Tuple[bool, str]:
    """Get human-readable time until target datetime."""
    now = datetime.now(target_datetime.tzinfo)
    
    if target_datetime <= now:
        return False, "Time has passed"
    
    delta = target_datetime - now
    
    if delta.days > 0:
        return True, f"{delta.days} days, {delta.seconds // 3600} hours"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return True, f"{hours} hours, {minutes} minutes"
    else:
        minutes = delta.seconds // 60
        return True, f"{minutes} minutes"

def is_time_in_range(check_time: time, start_time: time, end_time: time) -> bool:
    """Check if time is within a range."""
    if start_time <= end_time:
        return start_time <= check_time <= end_time
    else:  # Range crosses midnight
        return check_time >= start_time or check_time <= end_time