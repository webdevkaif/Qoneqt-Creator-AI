from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.utils.voice_module import generate_speech
from app.core.config import settings
from pathlib import Path
import time

router = APIRouter(prefix="/voice", tags=["voice"])

class VoiceRequest(BaseModel):
    text: str
    voice: str = "en-US-AriaNeural"

@router.post("/generate")
async def create_voice(request: VoiceRequest):
    """
    Generate Text-to-Speech audio using the voice module.
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="Text is required")
        
    filename = f"tts_{int(time.time())}.mp3"
    output_path = str(Path(settings.LOCAL_STORAGE_PATH) / "audio" / filename)
    
    try:
        await generate_speech(request.text, request.voice, output_path)
        
        # Return URL to access the audio
        audio_url = f"/storage/audio/{filename}"
        return {"status": "success", "audio_url": audio_url, "file_path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
