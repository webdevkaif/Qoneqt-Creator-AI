from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional
import pymongo


class Scene(Document):
    project_id: str
    owner_id: str
    order: int
    narration: str
    visual_prompt: str
    duration: float = 3.0  # seconds
    caption: Optional[str] = None
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    video_clip_url: Optional[str] = None
    video_clip_path: Optional[str] = None
    audio_url: Optional[str] = None
    audio_path: Optional[str] = None
    generation_status: str = "pending"  # pending | generating | done | failed
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "scenes"
        indexes = [
            [("project_id", pymongo.ASCENDING), ("order", pymongo.ASCENDING)],
        ]
