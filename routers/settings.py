from fastapi import APIRouter, HTTPException, Body
import requests
import os
from utils.firestore import update_user_voice, get_user_voice

router = APIRouter()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

@router.get("/voices")
async def list_available_voices():
    """Fetch and filter soothing/wellness voices from ElevenLabs"""
    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": ELEVENLABS_API_KEY}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch voices from ElevenLabs")
        
        all_voices = response.json().get("voices", [])
        
        # Filter for voices that fit the Tulizo vibe (calm, soothing, pleasant)
        curated_voices = []
        for v in all_voices:
            labels = str(v.get("labels", {})).lower()
            if any(tag in labels for tag in ["calm", "soothing", "soft", "warm", "gentle"]):
                curated_voices.append({
                    "voice_id": v["voice_id"],
                    "name": v["name"],
                    "preview_url": v["preview_url"],
                    "category": v["category"],
                    "description": v.get("description", "A soothing Tulizo voice")
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