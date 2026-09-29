from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, Any, Dict
from enum import Enum
import pymongo


class JobType(str, Enum):
    SCRIPT = "script"
    STORYBOARD = "storyboard"
    IMAGE = "image"
    TTS = "tts"
    VIDEO_RENDER = "video_render"
    SCENE_REGEN = "scene_regen"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GenerationJob(Document):
    project_id: str
    owner_id: str
    job_type: JobType
    celery_task_id: Optional[str] = None
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0  # 0-100
    progress_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Settings:
        name = "generation_jobs"
        indexes = [
            [("project_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
            [("celery_task_id", pymongo.ASCENDING)],
            [("status", pymongo.ASCENDING)],
        ]
