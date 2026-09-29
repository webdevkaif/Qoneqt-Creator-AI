from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional
from enum import Enum
import pymongo


class PublishStatus(str, Enum):
    PENDING = "pending"
    MANUAL = "manual"  # user will publish manually
    PUBLISHED = "published"
    FAILED = "failed"


class PublishRecord(Document):
    project_id: str
    owner_id: str
    platform: str = "qoneqt"
    status: PublishStatus = PublishStatus.PENDING
    title: str
    description: Optional[str] = None
    hashtags: list = []
    video_url: Optional[str] = None
    external_post_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    class Settings:
        name = "publish_records"
        indexes = [
            [("project_id", pymongo.ASCENDING)],
        ]
