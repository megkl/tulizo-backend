from fastapi import APIRouter, HTTPException, Body
import requests
import os
from utils.firestore import update_user_voice, get_user_voice

router = APIRouter()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DEFAULT_VOICE_ID = os.getenv("VOICE_ID")

@router.get("/voices")
async def list_available_voices():
    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": ELEVENLABS_API_KEY}
        )
        all_voices = response.json().get("voices", [])
        
        # 1. Start with the "System Default" voice option
        curated_voices = [{
            "voice_id": DEFAULT_VOICE_ID,
            "name": "Tulizo Default (Recommended)",
            "preview_url": None, # Or fetch specific preview if known
            "category": "default",
            "description": "The original Tulizo AI persona."
        }]
        
        # 2. Add filtered curated voices
        for v in all_voices:
            # Avoid duplicating the default if it exists in the API list
            if v["voice_id"] == DEFAULT_VOICE_ID: continue
            
            labels = str(v.get("labels", {})).lower()
            # Expanded tags for more variety
            tags = ["calm", "soothing", "soft", "warm", "gentle", "wellness", "meditation", "relaxing", "narrative", "expressive"]
            if any(tag in labels for tag in tags):
                curated_voices.append({
                    "voice_id": v["voice_id"],
                    "name": v["name"],
                    "preview_url": v["preview_url"],
                    "category": v["category"],
                    "description": v.get("description", "Soothing Tulizo voice")
                })
        
        return {"status": "success", "voices": curated_voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/preference/{user_id}")
async def fetch_preference(user_id: str):
    pref = get_user_voice(user_id)
    return {"status": "success", "preference": pref}

@router.post("/save")
async def save_voice_preference(
    user_id: str = Body(...),
    voice_id: str = Body(...),
    voice_name: str = Body(...)
):
    success = update_user_voice(user_id, voice_id, voice_name)
    if success:
        return {"status": "success", "message": "Voice preference updated"}
    raise HTTPException(status_code=500, detail="Failed to save settings")