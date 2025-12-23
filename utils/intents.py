import re
from datetime import datetime

# --- Mood Detection ---
def extract_mood(user_message):
    """
    Extracts mood from natural language. Returns mood as a string or number.
    Examples:
        "I'm feeling sad" -> "sad"
        "Feeling 8 out of 10" -> 8
    """
    # Check for numeric mood
    numeric_match = re.search(r'\b([1-9]|10)\b', user_message)
    if numeric_match:
        return int(numeric_match.group(0))

    # Check for common mood keywords
    mood_keywords = ["happy", "sad", "anxious", "angry", "stressed", "excited", "tired", "relaxed"]
    for word in mood_keywords:
        if word in user_message.lower():
            return word

    return None

# --- Task Detection ---
def extract_task(user_message):
    """
    Extracts tasks/reminders from text.
    Examples:
        "Remind me to call John at 3 PM" -> "call John at 3 PM"
    """
    task_patterns = [
        r"remind me to (.+)",
        r"i need to (.+)",
        r"don't forget to (.+)",
    ]
    for pattern in task_patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

# --- Due Date Extraction (optional, simple) ---
def extract_due_date(user_message):
    # Simple example: look for "at TIME" or "by DATE"
    time_match = re.search(r'\bat (\d{1,2}(:\d{2})?\s?(AM|PM)?)\b', user_message, re.IGNORECASE)
    if time_match:
        return time_match.group(1)
    return None
