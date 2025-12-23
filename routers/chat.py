from fastapi import APIRouter, Request
from utils.firestore import save_conversation, get_recent_conversations
import base64
import requests
import os
from google import genai

router = APIRouter()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client = genai.Client()

@router.post("/")
async def chat(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    user_message = data.get("message", "").strip()

    if not user_message:
        return {"error": "Message cannot be empty."}

    try:
        gemini_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"You are Tulizo AI, an empathetic productivity assistant. Respond kindly to: {user_message}"
        )
        ai_text = gemini_response.text
    except Exception as e:
        return {"text": f"Error with Gemini API: {str(e)}", "audio": ""}

    # ElevenLabs TTS
    audio_base64 = ""
    try:
        voice_id = data.get("voice_id") or "default_voice_id"
        voice_response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
            json={"text": ai_text, "voice_settings": {"stability":0.5,"similarity_boost":0.8}},
        )
        if voice_response.status_code == 200:
            audio_base64 = base64.b64encode(voice_response.content).decode("utf-8")
    except Exception as e:
        print("TTS error:", e)

    # Save conversation
    try:
        save_conversation(user_id, user_message, ai_text)
    except Exception as e:
        print("Firestore save error:", e)

    return {"text": ai_text, "audio": audio_base64}

@router.get("/history")
def history(user_id: str, limit: int = 5):
    try:
        conversations = get_recent_conversations(user_id, limit)
        return {"status": "success", "conversations": conversations}
    except Exception as e:
        return {"status": "error", "message": str(e)}
