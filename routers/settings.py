from fastapi import APIRouter, Request
from utils.firestore import update_voice, get_voice

router = APIRouter()

@router.post("/voice")
async def set_voice(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    voice_id = data.get("voice_id")

    if not user_id or not voice_id:
        return {"error": "user_id and voice_id are required"}

    update_voice(user_id, voice_id)
    return {"status": "success", "voice_id": voice_id}


@router.get("/voice")
def get_user_voice(user_id: str):
    if not user_id:
        return {"error": "user_id is required"}

    voice_id = get_voice(user_id)
    return {"status": "success", "voice_id": voice_id}
