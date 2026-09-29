from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional
from enum import Enum
import pymongo


class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO_CLIP = "video_clip"
    AUDIO = "audio"
    SUBTITLE = "subtitle"
    FINAL_VIDEO = "final_video"
    THUMBNAIL = "thumbnail"


class Asset(Document):
    project_id: str
    scene_id: Optional[str] = None
    owner_id: str
    asset_type: AssetType
    file_path: str
    file_url: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    provider: Optional[str] = None  # openai, stability, elevenlabs, demo, upload
    prompt_used: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "assets"
        indexes = [
            [("project_id", pymongo.ASCENDING)],
            [("scene_id", pymongo.ASCENDING)],
        ]
