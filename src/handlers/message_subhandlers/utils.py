import re

def sanitize_text(text):
    """Remove HTML tags and URLs from text."""
    if not text: return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove URLs
    text = re.sub(r"http[s]?://\S+", "", text)
    return text.strip()


def extract_license_key(text):
    """Extract license key from message text. Format: WLB-xxxx-xxxx-xxxx-xxxx"""
    if not text:
        return None

    # Look for WLB-xxxx-xxxx-xxxx-xxxx pattern
    pattern = r'WLB-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}'
    match = re.search(pattern, text.upper())
    return match.group(0) if match else None