from fastapi import FastAPI, Request, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from google import genai  # Gemini SDK
from utils.firestore import save_conversation, get_recent_conversations, get_tasks, create_task, delete_task, get_user_voice, update_user_voice, save_mood_entry, get_mood_trends
from routers import chat, tasks, settings, analytics, dashboard

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
user_pref = get_user_voice("meg123")
# VOICE_ID = os.getenv("VOICE_ID")
VOICE_ID = user_pref["voice_id"] if user_pref else os.getenv("VOICE_ID")

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

    if not user_id: return {"error": "user_id is required."}
    if not user_message: return {"error": "Message cannot be empty."}

    action_intent = "CHAT"
    ai_text = ""
    mood_value = None
    sfx_prompt = None
    
    if "[MOOD_UPDATE]" in user_message:
        mood_value = user_message.split(":")[-1].strip().replace(".", "")
        action_intent = "MOOD_REFLECT"
        save_mood_entry(user_id, mood_value)
        
        # Define immersive soundscapes based on mood
        mood_sfx = {
            "COOL": "Calming forest rain with distant soft wind, high fidelity",
            "GOOD": "Soft morning birds chirping in a quiet garden",
            "MAD": "Steady ocean waves crashing softly on sand",
            "MEH": "Warm fireplace crackling in a quiet room"
        }
        sfx_prompt = mood_sfx.get(mood_value)
        
        # Specialized prompt for Gemini to respond to the mood
        system_prompt = f"The user is feeling {mood_value}. Give a warm, empathetic 1-sentence reflection as Tulizo AI."
    else:
        # Standard Task/Chat Prompt
        system_prompt = f"""
        You are Tulizo AI. User Message: "{user_message}"
        1. If [SYSTEM_EVENT: ALL_TASKS_DONE], start with [ACTION:VICTORY].
        2. If adding task, start with [ACTION:ADD].
        3. If deleting, start with [ACTION:DELETE].
        Otherwise, be supportive.
        """
    
    # Updated prompt to handle the Victory state
    prompt = f"""
    You are Tulizo AI. 
    User Message: "{user_message}"
    
    Instructions:
    1. If message is "[SYSTEM_EVENT: ALL_TASKS_DONE]", respond with a highly celebratory, proud, 1-sentence congrats. Start with [ACTION:VICTORY].
    2. If user wants to ADD a task, confirm warmly. Start with [ACTION:ADD].
    3. If user wants to DELETE/CLEAR completed tasks, confirm with relief. Start with [ACTION:DELETE].
    4. Otherwise, be supportive.
    """

    try:
        gemini_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw_response = gemini_response.text

       # Intent Parsing Logic
        if "[ACTION:VICTORY]" in raw_response:
            action_intent = "VICTORY"
            ai_text = raw_response.replace("[ACTION:VICTORY]", "").strip()
        elif "[ACTION:DELETE]" in raw_response:
            action_intent = "DELETE_COMPLETED"
            ai_text = raw_response.replace("[ACTION:DELETE]", "").strip()
        elif "[ACTION:ADD]" in raw_response:
            action_intent = "ADD_TASK"
            ai_text = raw_response.replace("[ACTION:ADD]", "").strip()
        else:
            ai_text = raw_response
            
    except Exception as e:
        print("Gemini API error:", e)
        # ai_text = "I'm so proud of your progress today!"

    stability_val = 0.3 if mood_value in ["ANGRY", "STRESSED"] else 0.6
    # --- Generate Voice (ElevenLabs) ---
    audio_base64 = ""
    try:
        voice_response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            json={"text": ai_text, "voice_settings": {"stability": 0.4, "similarity_boost": 0.8}}
        )
        if voice_response.status_code == 200:
            audio_base64 = base64.b64encode(voice_response.content).decode("utf-8")
        else:
                print("ElevenLabs error:", voice_response.text)
    except: pass

    # --- Specialized SFX Generation ---
    sfx_base64 = ""
    sfx_prompt = None
    if action_intent == "DELETE_COMPLETED":
        sfx_prompt = "Soft digital paper shredding and a clean chime"
    elif action_intent == "VICTORY":
        sfx_prompt = "A triumphant, sparkling orchestral chime, magical finish, high quality"

    if sfx_prompt:
        try:
            sfx_res = requests.post(
                "https://api.elevenlabs.io/v1/sound-generation",
                headers={"xi-api-key": ELEVENLABS_API_KEY},
                json={"text": sfx_prompt, "duration_seconds": 2.0}
            )
            if sfx_res.status_code == 200:
                sfx_base64 = base64.b64encode(sfx_res.content).decode("utf-8")
        except: pass

    save_conversation(user_id, user_message, ai_text, mood=mood_value)
    return {"text": ai_text, "audio": audio_base64, "sfx": sfx_base64, "action": action_intent}

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
    """
    Add a new task for a user — supports voice-based input
    and returns a spoken ElevenLabs confirmation.
    """
    data = await request.json()
    user_id = data.get("user_id")
    task_text = data.get("task_text")
    due_date = data.get("due_date")

    if not user_id or not task_text:
        return {"status": "error", "message": "user_id and task_text are required."}

    # --- Create task in Firestore ---
    try:
        task_id = create_task(user_id, task_text, due_date)
    except Exception as e:
        print("Firestore task create error:", e)
        return {"status": "error", "message": str(e)}

    # --- Tulizo's voice confirmation ---
    confirmation_text = f"I’ve added your task: {task_text}. Keep it up, you’re doing great!"
    audio_base64 = ""

    try:
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": confirmation_text,
                "voice_settings": {"stability": 0.6, "similarity_boost": 0.85},
            },
            timeout=10,
        )

        if response.status_code == 200:
            audio_base64 = base64.b64encode(response.content).decode("utf-8")
        else:
            print("ElevenLabs TTS error:", response.text)

    except Exception as e:
        print("ElevenLabs request failed:", e)

    # --- Return both voice + message ---
    return {
        "status": "success",
        "task_id": task_id,
        "message": confirmation_text,
        "audio": audio_base64,
}

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

@app.delete("/tasks/{task_id}")
async def remove_task(task_id: str, request: Request):
    """Delete a task from Firestore"""
    data = await request.json()
    user_id = data.get("user_id")

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required in the body")

    try:
        success = delete_task(user_id, task_id)
        if success:
            return {"status": "success", "message": f"Task {task_id} deleted."}
        else:
            raise HTTPException(status_code=404, detail="Task not found or could not be deleted.")
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def generate_confirmation_sfx(action_type: str):
    """Generates unique SFX for task actions"""
    prompts = {
        "added": "A soft, high-quality digital 'bloop' sound, satisfying and clean",
        "completed": "A magical shimmering chime, sparkling and triumphant",
        "deleted": "A low-frequency soft paper crumple sound"
    }
    
    prompt = prompts.get(action_type, "Soft notification ping")
    
    try:
        response = requests.post(
            "https://api.elevenlabs.io/v1/sound-generation",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            json={"text": prompt, "duration_seconds": 1.0}
        )
        return base64.b64encode(response.content).decode("utf-8")
    except:
        return ""

@app.post("/tasks/voice-add")
async def voice_add_task(request: Request):
    data = await request.json()
    raw_text = data.get("text")
    
    # 1. Use Gemini to categorize and generate a response
    prompt = f"""
    Analyze this task: "{raw_text}". 
    1. Categorize it as: "Work", "Personal", or "High Priority".
    2. Provide a 1-sentence empathetic confirmation.
    Return as JSON: {{"category": "...", "confirmation": "..."}}
    """
    ai_analysis = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    analysis_data = json.loads(ai_analysis.text)
    
    # 2. TTS with Emotion Tuning
    # Use higher stability for 'Work' tasks, more expression for 'Personal'
    stability = 0.7 if analysis_data['category'] == "Work" else 0.4
    
    voice_res = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        headers={"xi-api-key": ELEVENLABS_API_KEY},
        json={
            "text": analysis_data['confirmation'],
            "voice_settings": {"stability": stability, "similarity_boost": 0.8}
        }
    )
    
    audio_b64 = base64.b64encode(voice_res.content).decode("utf-8")
    return {**analysis_data, "audio": audio_b64}

@app.get("/analytics/trends")
def get_trends(user_id: str):
    """Aggregates Mood Scores and Task Completion % for the last 7 days"""
    try:
        # This function (defined in step 2) calculates the actual data from Firestore
        trends = get_mood_trends(user_id)
        return {"status": "success", "data": trends}
    except Exception as e:
        return {"status": "error", "message": str(e)}