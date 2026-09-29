from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
from typing import Optional
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from app.models.project import Project, ProjectStatus
from app.models.scene import Scene
from app.core.security import get_current_user_id
import copy

router = APIRouter(prefix="/projects", tags=["Projects"])


def _project_to_response(p: Project) -> ProjectResponse:
    return ProjectResponse(
        id=str(p.id),
        title=p.title,
        topic=p.topic,
        community=p.community,
        language=p.language,
        duration=p.duration,
        aspect_ratio=p.aspect_ratio,
        style=p.style,
        status=p.status,
        thumbnail_url=p.thumbnail_url,
        video_url=p.video_url,
        video_title=p.video_title,
        video_description=p.video_description,
        hashtags=p.hashtags,
        script=p.script,
        error_message=p.error_message,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, user_id: str = Depends(get_current_user_id)):
    project = Project(
        owner_id=user_id,
        title=data.title,
        topic=data.topic,
        community=data.community,
        language=data.language,
        duration=data.duration,
        aspect_ratio=data.aspect_ratio,
        style=data.style,
        voice_id=data.voice_id,
        enable_subtitles=data.enable_subtitles,
        enable_narration=data.enable_narration,
        custom_community=data.custom_community,
        description=data.description,
    )
    await project.save()
    return _project_to_response(project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "-created_at",
    user_id: str = Depends(get_current_user_id),
):
    query = {"owner_id": user_id}
    if status:
        query["status"] = status
    if search:
        query["title"] = {"$regex": search, "$options": "i"}

    total = await Project.find(query).count()
    sort_field = sort.lstrip("-")
    sort_dir = -1 if sort.startswith("-") else 1
    projects = await (
        Project.find(query)
        .sort([(sort_field, sort_dir)])
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )
    return ProjectListResponse(
        projects=[_project_to_response(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, user_id: str = Depends(get_current_user_id)):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_response(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str, data: ProjectUpdate, user_id: str = Depends(get_current_user_id)
):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = data.model_dump(exclude_none=True)
    for k, v in update_data.items():
        setattr(project, k, v)
    project.updated_at = datetime.utcnow()
    await project.save()
    return _project_to_response(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, user_id: str = Depends(get_current_user_id)):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    await Scene.find({"project_id": project_id}).delete()
    await project.delete()


@router.post("/{project_id}/duplicate", response_model=ProjectResponse, status_code=201)
async def duplicate_project(project_id: str, user_id: str = Depends(get_current_user_id)):
    original = await Project.get(project_id)
    if not original or str(original.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")

    dup = Project(
        owner_id=user_id,
        title=f"Copy of {original.title}",
        topic=original.topic,
        community=original.community,
        language=original.language,
        duration=original.duration,
        aspect_ratio=original.aspect_ratio,
        style=original.style,
        voice_id=original.voice_id,
        enable_subtitles=original.enable_subtitles,
        enable_narration=original.enable_narration,
        description=original.description,
    )
    await dup.save()
    return _project_to_response(dup)
