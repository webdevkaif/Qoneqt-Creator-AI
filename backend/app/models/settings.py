from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional
import pymongo


class UserSettings(Document):
    user_id: Indexed(str, unique=True)
    preferred_language: str = "en"
    preferred_voice: str = "alloy"
    default_community: str = "Technology"
    default_style: str = "Educational"
    default_duration: int = 30
    enable_subtitles: bool = True
    enable_narration: bool = True
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "user_settings"
