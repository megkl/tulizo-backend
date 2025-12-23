from fastapi import APIRouter, Request
from utils.firestore import get_recent_conversations
from datetime import datetime

router = APIRouter()

@router.get("/mood")
async def get_mood(user_id: str, limit: int = 30):
    """
    Fetch the user's recent mood scores.
    Returns a list of {timestamp, mood_score}.
    """
    try:
        conversations = get_recent_conversations(user_id, limit)
        mood_logs = []
        for conv in conversations:
            if conv.get("mood") is not None:
                # Ensure mood is numeric
                mood_score = conv["mood"]
                if isinstance(mood_score, int) or isinstance(mood_score, float):
                    mood_logs.append({
                        "timestamp": conv["timestamp"].isoformat() if hasattr(conv["timestamp"], "isoformat") else conv["timestamp"],
                        "mood_score": mood_score
                    })
        # Sort by timestamp ascending
        mood_logs.sort(key=lambda x: x["timestamp"])
        return {"moods": mood_logs}
    except Exception as e:
        return {"error": str(e)}
