from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.job import JobType, JobStatus


class JobResponse(BaseModel):
    id: str
    project_id: str
    job_type: JobType
    status: JobStatus
    progress: int
    progress_message: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PublishRequest(BaseModel):
    title: str
    description: Optional[str] = None
    hashtags: list = []


class PublishResponse(BaseModel):
    id: str
    project_id: str
    status: str
    platform: str
    manual_workflow: bool = True
    qoneqt_url: Optional[str] = None
    message: str
