from beanie import Document, Link, Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import pymongo
from bson import ObjectId


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"
    PUBLISHED = "published"


class Community(str, Enum):
    TECHNOLOGY = "Technology"
    EDUCATION = "Education"
    GAMING = "Gaming"
    FITNESS = "Fitness"
    SCIENCE = "Science"
    ENTERTAINMENT = "Entertainment"
    BUSINESS = "Business"
    CUSTOM = "Custom"


class VideoStyle(str, Enum):
    EDUCATIONAL = "Educational"
    CINEMATIC = "Cinematic"
    MOTIVATIONAL = "Motivational"
    STORYTELLING = "Storytelling"
    NEWS_EXPLAINER = "News Explainer"
    ANIMATED = "Animated"


class AspectRatio(str, Enum):
    PORTRAIT = "9:16"
    LANDSCAPE = "16:9"
    SQUARE = "1:1"


class Project(Document):
    owner_id: str
    title: str
    description: Optional[str] = None
    topic: str
    community: Community = Community.TECHNOLOGY
    language: str = "en"
    duration: int = 30  # seconds
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT
    style: VideoStyle = VideoStyle.EDUCATIONAL
    voice_id: Optional[str] = None
    enable_subtitles: bool = True
    enable_narration: bool = True
    custom_community: Optional[str] = None

    # Script / content
    script: Optional[dict] = None
    video_title: Optional[str] = None
    video_description: Optional[str] = None
    hashtags: List[str] = []

    # Assets
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    video_path: Optional[str] = None
    subtitle_url: Optional[str] = None

    # Status
    status: ProjectStatus = ProjectStatus.DRAFT
    current_job_id: Optional[str] = None
    error_message: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "projects"
        indexes = [
            [("owner_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
            [("status", pymongo.ASCENDING)],
        ]
