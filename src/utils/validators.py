import re

BANNED_WORDS = [
    'fuck', 'shit', 'bitch', 'asshole', 'bastard', 'damn', 'hell', 'crap',
    'dick', 'pussy', 'cock', 'whore', 'slut', 'motherfucker', 'retard',
    'idiot', 'stupid', 'dumb', 'loser', 'ugly', 'hate', 'kill', 'die',
    'chutiya', 'madarchod', 'bhenchod', 'gaandu', 'harami', 'kamina',
    'kutta', 'kutti', 'saala', 'saali', 'bhadwa', 'randi', 'lodu',
    'gandu', 'jhia', 'banda', 'gadha', 'pagal', 'nalayak',
    'porn', 'sex', 'nude', 'naked', 'xxx', 'adult', 'nsfw',
    'suicide', 'violence', 'rape', 'murder', 'terrorist', 'bomb',
]

def contains_banned_word(text, custom_banned_words=None):
    if not text:
        return False, None
    
    text_lower = text.lower()
    
    for word in BANNED_WORDS:
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text_lower):
            return True, word
    
    if custom_banned_words:
        for word in custom_banned_words:
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            if re.search(pattern, text_lower):
                return True, word
    
    return False, None

def validate_username(username):
    if not username:
        return False
    
    username = username.lstrip('@')
    pattern = r'^[a-zA-Z0-9_]{5,32}$'
    return bool(re.match(pattern, username))

def validate_group_id(group_id):
    try:
        gid = int(group_id)
        return gid < 0
    except ValueError:
        return False

def validate_user_id(user_id):
    try:
        uid = int(user_id)
        return uid > 0
    except ValueError:
        return False

def validate_points(points):
    try:
        points_int = int(points)
        if points_int >= 0:
            return points_int
    except ValueError:
        pass
    return None

def sanitize_text(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    return text.strip()

def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename

def validate_time_format(time_str):
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$|^([0-1]?[0-9]|2[0-3])$'
    return bool(re.match(pattern, time_str))