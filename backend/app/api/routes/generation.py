"""
Generation API — triggers background jobs for script, visuals, TTS, and video rendering.
Returns job IDs for polling. Prevents duplicate submissions.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from datetime import datetime
from typing import Optional
from app.models.project import Project, ProjectStatus
from app.models.scene import Scene
from app.models.job import GenerationJob, JobType, JobStatus
from app.schemas.job import JobResponse
from app.schemas.scene import SceneResponse, SceneUpdate
from app.core.security import get_current_user_id
from app.workers.tasks import generate_script_task, generate_visuals_task, generate_tts_task, render_video_task
from loguru import logger

router = APIRouter(prefix="/generate", tags=["Generation"])
UPLOAD_MAX_BYTES = 50 * 1024 * 1024  # 50 MB


async def _create_job(project_id: str, owner_id: str, job_type: JobType) -> GenerationJob:
    # Check for running duplicate
    existing = await GenerationJob.find_one({
        "project_id": str(project_id),
        "job_type": job_type.value,
        "status": {"$in": ["queued", "running"]},
    })
    if existing:
        raise HTTPException(status_code=409, detail=f"A {job_type.value} job is already running for this project")

    job = GenerationJob(
        project_id=str(project_id),
        owner_id=str(owner_id),
        job_type=job_type,
    )
    await job.save()
    return job


def _job_to_response(job: GenerationJob) -> JobResponse:
    return JobResponse(
        id=str(job.id),
        project_id=job.project_id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        progress_message=job.progress_message,
        error=job.error,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.post("/script/{project_id}", response_model=JobResponse, status_code=202)
async def start_script_generation(project_id: str, user_id: str = Depends(get_current_user_id)):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")

    job = await _create_job(project_id, user_id, JobType.SCRIPT)
    task = generate_script_task.apply_async(args=[str(job.id), project_id, user_id])
    job.celery_task_id = task.id
    await job.save()
    return _job_to_response(job)


@router.post("/visuals/{project_id}", response_model=JobResponse, status_code=202)
async def start_visual_generation(project_id: str, user_id: str = Depends(get_current_user_id)):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.script:
        raise HTTPException(status_code=400, detail="Generate a script first")

    job = await _create_job(project_id, user_id, JobType.IMAGE)
    task = generate_visuals_task.apply_async(args=[str(job.id), project_id, user_id])
    job.celery_task_id = task.id
    await job.save()
    return _job_to_response(job)


@router.post("/narration/{project_id}", response_model=JobResponse, status_code=202)
async def start_tts_generation(project_id: str, user_id: str = Depends(get_current_user_id)):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.script:
        raise HTTPException(status_code=400, detail="Generate a script first")

    job = await _create_job(project_id, user_id, JobType.TTS)
    task = generate_tts_task.apply_async(args=[str(job.id), project_id, user_id])
    job.celery_task_id = task.id
    await job.save()
    return _job_to_response(job)


@router.post("/render/{project_id}", response_model=JobResponse, status_code=202)
async def start_video_render(project_id: str, user_id: str = Depends(get_current_user_id)):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.script:
        raise HTTPException(status_code=400, detail="Generate a script first")

    scenes = await Scene.find({"project_id": project_id}).count()
    if scenes == 0:
        raise HTTPException(status_code=400, detail="No scenes found. Generate a script first.")

    job = await _create_job(project_id, user_id, JobType.VIDEO_RENDER)
    task = render_video_task.apply_async(args=[str(job.id), project_id, user_id])
    job.celery_task_id = task.id
    await job.save()
    return _job_to_response(job)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        from bson import ObjectId
        if ObjectId.is_valid(job_id):
            job = await GenerationJob.get(job_id)
        else:
            job = await GenerationJob.find_one({"_id": job_id})
    except Exception:
        job = None

    if not job or str(job.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)


@router.get("/jobs/project/{project_id}")
async def get_project_jobs(project_id: str, user_id: str = Depends(get_current_user_id)):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    jobs = await GenerationJob.find({"project_id": str(project_id)}).sort("-created_at").to_list()
    return [_job_to_response(j) for j in jobs]


@router.get("/scenes/{project_id}")
async def get_scenes(project_id: str, user_id: str = Depends(get_current_user_id)):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    scenes = await Scene.find({"project_id": project_id}).sort("+order").to_list()
    return [
        SceneResponse(
            id=str(s.id), project_id=s.project_id, order=s.order,
            narration=s.narration, visual_prompt=s.visual_prompt,
            duration=s.duration, caption=s.caption,
            image_url=s.image_url, video_clip_url=s.video_clip_url,
            audio_url=s.audio_url, generation_status=s.generation_status,
            error_message=s.error_message,
            created_at=s.created_at, updated_at=s.updated_at,
        )
        for s in scenes
    ]


@router.patch("/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: str, data: SceneUpdate, user_id: str = Depends(get_current_user_id)
):
    scene = await Scene.get(scene_id)
    if not scene or scene.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Scene not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(scene, k, v)
    scene.updated_at = datetime.utcnow()
    await scene.save()
    return SceneResponse(
        id=str(scene.id), project_id=scene.project_id, order=scene.order,
        narration=scene.narration, visual_prompt=scene.visual_prompt,
        duration=scene.duration, caption=scene.caption,
        image_url=scene.image_url, video_clip_url=scene.video_clip_url,
        audio_url=scene.audio_url, generation_status=scene.generation_status,
        error_message=scene.error_message,
        created_at=scene.created_at, updated_at=scene.updated_at,
    )


@router.post("/scenes/{scene_id}/upload-image")
async def upload_scene_image(
    scene_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    scene = await Scene.get(scene_id)
    if not scene or scene.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Scene not found")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    data = await file.read()
    if len(data) > UPLOAD_MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    from app.utils.storage import save_file
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    path, url = await save_file(data, user_id, scene.project_id, f"upload_{scene_id}.{ext}", subdir="uploads")

    scene.image_path = path
    scene.image_url = url
    scene.generation_status = "done"
    scene.updated_at = datetime.utcnow()
    await scene.save()

    return {"image_url": url, "scene_id": scene_id}
