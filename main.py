from fastapi import FastAPI, Request, Body
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from google import genai  # Gemini SDK
from utils.firestore import save_conversation, get_recent_conversations, get_tasks, create_task
from routers import chat, tasks, settings, analytics, dashboard
from utils.intents import extract_mood, extract_task, extract_due_date
import requests
import base64

load_dotenv()

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API keys
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")

# Gemini client (auto-uses GEMINI_API_KEY)
client = genai.Client()

app.include_router(chat.router, prefix="/chat")
app.include_router(tasks.router, prefix="/tasks")
app.include_router(settings.router, prefix="/settings")
app.include_router(analytics.router, prefix="/analytics")
app.include_router(dashboard.router, prefix="/dashboard")

@app.get("/")
def root():
    return {"message": "Tulizo AI backend running!"}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    user_message = data.get("message", "").strip()

    if not user_id:
        return {"error": "user_id is required."}
    if not user_message:
        return {"error": "Message cannot be empty."}

    # --- Generate AI response ---
    ai_text = ""
    try:
        gemini_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"You are Tulizo AI, an empathetic productivity assistant. Respond kindly to: {user_message}",
        )
        ai_text = gemini_response.text
    except Exception as e:
        error_message = str(e)
        print("Gemini API error:", error_message)
        if "RESOURCE_EXHAUSTED" in error_message:
            ai_text = "[Gemini API quota exceeded. Please try again later.]"
        else:
            ai_text = f"[Error with Gemini API: {error_message}]"

    # --- Convert AI text to voice ---
    audio_base64 = ""
    if ai_text and not ai_text.startswith("["):
        try:
            voice_response = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "text": ai_text,
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
                },
                timeout=10,
            )
            if voice_response.status_code == 200:
                audio_base64 = base64.b64encode(voice_response.content).decode("utf-8")
            else:
                print("ElevenLabs error:", voice_response.text)
        except Exception as e:
            print("ElevenLabs request failed:", e)

    # --- Save to Firestore ---
    try:
        save_conversation(user_id, user_message, ai_text)
    except Exception as e:
        print("Firestore save error:", e)

    return {"text": ai_text, "audio": audio_base64}

@app.get("/history")
def get_history(user_id: str, limit: int = 5):
    """Fetch the most recent Tulizo conversations from Firestore for a specific user."""
    if not user_id:
        return {"status": "error", "message": "user_id is required."}

    try:
        conversations = get_recent_conversations(user_id, limit)
        return {"status": "success", "conversations": conversations}
    except Exception as e:
        print("Firestore history fetch error:", e)
        return {"status": "error", "message": str(e)}

@app.get("/tasks")
def list_tasks(user_id: str):
    """Retrieve all tasks for a user"""
    if not user_id:
        return {"status": "error", "message": "user_id is required."}

    try:
        tasks = get_tasks(user_id)
        return {"status": "success", "tasks": tasks}
    except Exception as e:
        print("Firestore tasks fetch error:", e)
        return {"status": "error", "message": str(e)}

@app.post("/tasks")
async def add_task(request: Request):
    """Add a new task for a user"""
    data = await request.json()
    user_id = data.get("user_id")
    task_text = data.get("task_text")
    due_date = data.get("due_date")

    if not user_id or not task_text:
        return {"status": "error", "message": "user_id and task_text are required."}

    try:
        task_id = create_task(user_id, task_text, due_date)
        return {"status": "success", "task_id": task_id}
    except Exception as e:
        print("Firestore task create error:", e)
        return {"status": "error", "message": str(e)}

@app.post("/tasks/update")
async def update_task(
    task_id: str = Body(...),
    task_text: str | None = Body(None),
    due_date: str | None = Body(None),
    status: str | None = Body(None),
    user_id: str = Body(...),
):
    """Update an existing task"""
    from utils.firestore import update_task  # make sure this exists

    if not user_id or not task_id:
        return {"status": "error", "message": "user_id and task_id are required."}

    try:
        updated_task = update_task(user_id, task_id, task_text, due_date, status)
        return {"status": "success", "task": updated_task}
    except Exception as e:
        print("Firestore task update error:", e)
        return {"status": "error", "message": str(e)}
