from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.adapters.factory import get_image_adapter, get_tts_adapter
from app.utils.storage import save_file, ensure_storage_dirs
from app.utils.ffmpeg_utils import assemble_video
import tempfile
import os

router = APIRouter(prefix="/instant", tags=["Instant Generation"])

class InstantVideoRequest(BaseModel):
    content: str
    style: str = "cinematic"
    voice_id: str = "en-US-AriaNeural"

@router.post("/animate")
async def instant_animate(request: InstantVideoRequest):
    """
    Instantly converts text content to a visual and animated video.
    """
    ensure_storage_dirs()
    
    try:
        # 1. Generate Image from content
        img_adapter = get_image_adapter()
        img_bytes, ext = await img_adapter.generate_image(
            prompt=request.content,
            style=request.style,
            aspect_ratio="9:16"
        )
        
        # Save temporary image
        img_tmp = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False)
        img_tmp.write(img_bytes)
        img_tmp.close()
        
        # 2. Generate Audio TTS
        tts_adapter = get_tts_adapter()
        audio_bytes = await tts_adapter.generate_speech(
            text=request.content,
            voice_id=request.voice_id,
            language="en"
        )
        
        audio_tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        audio_tmp.write(audio_bytes)
        audio_tmp.close()
        
        # 3. Assemble Video
        video_tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        video_tmp.close()
        
        scenes = [{
            "image_path": img_tmp.name,
            "audio_path": audio_tmp.name,
            "duration": 5.0, # Will be adjusted by ffmpeg to match audio length
            "narration": request.content,
            "caption": request.content
        }]
        
        async def progress_cb(pct, msg):
            pass
            
        success, error = await assemble_video(
            scenes=scenes,
            output_path=video_tmp.name,
            aspect_ratio="9:16",
            audio_path=None, # It uses scene audio
            subtitle_path=None,
            progress_callback=progress_cb
        )
        
        # Cleanup temp files
        os.unlink(img_tmp.name)
        os.unlink(audio_tmp.name)
        
        if not success:
            os.unlink(video_tmp.name)
            raise HTTPException(status_code=500, detail=error)
            
        # Read generated video and save to persistent storage
        with open(video_tmp.name, "rb") as f:
            video_data = f.read()
        os.unlink(video_tmp.name)
        
        # Use a dummy user/project id since it's instant
        video_path, video_url = await save_file(
            video_data, "instant_user", "instant_project", "animated_video.mp4", subdir="videos"
        )
        
        return {
            "status": "success",
            "message": "Content converted to animated video",
            "video_url": video_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
