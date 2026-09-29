from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.project import ProjectStatus, Community, VideoStyle, AspectRatio


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    topic: str = Field(..., min_length=3, max_length=1000)
    community: Community = Community.TECHNOLOGY
    language: str = "en"
    duration: int = Field(30, ge=15, le=60)
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT
    style: VideoStyle = VideoStyle.EDUCATIONAL
    voice_id: Optional[str] = None
    enable_subtitles: bool = True
    enable_narration: bool = True
    custom_community: Optional[str] = None
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    topic: Optional[str] = None
    community: Optional[Community] = None
    language: Optional[str] = None
    duration: Optional[int] = Field(None, ge=15, le=60)
    aspect_ratio: Optional[AspectRatio] = None
    style: Optional[VideoStyle] = None
    voice_id: Optional[str] = None
    enable_subtitles: Optional[bool] = None
    enable_narration: Optional[bool] = None
    description: Optional[str] = None
    script: Optional[dict] = None
    video_title: Optional[str] = None
    video_description: Optional[str] = None
    hashtags: Optional[List[str]] = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    topic: str
    community: Community
    language: str
    duration: int
    aspect_ratio: AspectRatio
    style: VideoStyle
    status: ProjectStatus
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    video_title: Optional[str] = None
    video_description: Optional[str] = None
    hashtags: List[str] = []
    script: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int
