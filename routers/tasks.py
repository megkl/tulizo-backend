from fastapi import APIRouter, Request
from utils.firestore import create_task, get_tasks
from datetime import datetime

router = APIRouter()

@router.post("/")
async def add_task(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    task_text = data.get("task_text")
    due_date = data.get("due_date")  # expected ISO string

    if not user_id or not task_text:
        return {"error": "user_id and task_text are required"}

    due_dt = datetime.fromisoformat(due_date) if due_date else None
    task_id = create_task(user_id, task_text, due_dt)
    return {"status": "success", "task_id": task_id}


@router.get("/")
def list_tasks(user_id: str):
    if not user_id:
        return {"error": "user_id is required"}
    print(user_id)
    tasks = get_tasks(user_id)
    return {"status": "success", "tasks": tasks}
