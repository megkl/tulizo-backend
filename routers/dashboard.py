from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from utils.firestore import (
    create_task,
    get_tasks,
    get_user_voice,
    update_user_voice,
    save_conversation,
)

router = APIRouter(prefix="/user", tags=["User"])

# --- Schemas ---
class TaskCreate(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    task_text: str = Field(..., description="Description of the user's task")
    due_date: Optional[str] = Field(None, description="Task due date in ISO 8601 format")


class VoiceUpdate(BaseModel):
    user_id: str
    voice_id: str


class MoodLog(BaseModel):
    user_id: str
    mood: int = Field(..., ge=1, le=10, description="Mood level from 1 (low) to 10 (high)")


# --- Tasks ---
@router.post("/tasks")
def add_task(task: TaskCreate):
    """Add a new task for a user"""
    try:
        task_id = create_task(task.user_id, task.task_text, task.due_date)
        return {"status": "success", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {e}")


@router.get("/tasks")
def fetch_tasks(user_id: str):
    """Retrieve all tasks for a user"""
    try:
        tasks = get_tasks(user_id)
        return {"status": "success", "tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {e}")


# --- Voice Settings ---
@router.post("/voice")
def set_voice(data: VoiceUpdate):
    """Update a user's preferred voice"""
    try:
        update_user_voice(data.user_id, data.voice_id)
        return {"status": "success", "message": "Voice preference updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update voice: {e}")


@router.get("/voice")
def get_user_voice(user_id: str):
    """Retrieve a user's preferred voice"""
    try:
        voice_id = get_user_voice(user_id)
        return {"status": "success", "voice": voice_id or "default"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch voice: {e}")


# --- Mood Logging ---
@router.post("/mood")
def log_mood(data: MoodLog):
    """Log user's mood entry"""
    try:
        save_conversation(
            user_id=data.user_id,
            user_message="Mood log",
            ai_response="",
            mood=data.mood,
        )
        return {"status": "success", "message": "Mood logged successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log mood: {e}")
