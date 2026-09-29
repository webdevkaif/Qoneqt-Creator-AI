from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SceneUpdate(BaseModel):
    narration: Optional[str] = None
    visual_prompt: Optional[str] = None
    duration: Optional[float] = Field(None, ge=1.0, le=30.0)
    caption: Optional[str] = None
    order: Optional[int] = None


class SceneResponse(BaseModel):
    id: str
    project_id: str
    order: int
    narration: str
    visual_prompt: str
    duration: float
    caption: Optional[str] = None
    image_url: Optional[str] = None
    video_clip_url: Optional[str] = None
    audio_url: Optional[str] = None
    generation_status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
