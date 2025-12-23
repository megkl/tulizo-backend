from fastapi import APIRouter
from utils.firestore import get_recent_conversations, get_tasks
from collections import Counter

router = APIRouter()

@router.get("/mood_trends")
def mood_trends(user_id: str, limit: int = 100):
    """Return mood counts for the last `limit` conversations"""
    conversations = get_recent_conversations(user_id, limit)
    moods = [c.get("mood") for c in conversations if c.get("mood")]
    trend = dict(Counter(moods))
    return {"status": "success", "mood_trends": trend}

@router.get("/task_stats")
def task_stats(user_id: str):
    """Return counts of completed and pending tasks"""
    tasks = get_tasks(user_id)
    completed = sum(1 for t in tasks if t.get("status") == "completed")
    pending = sum(1 for t in tasks if t.get("status") == "pending")
    return {"status": "success", "completed": completed, "pending": pending}
