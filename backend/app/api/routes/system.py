from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from app.models.project import Project
from app.core.security import get_current_user_id
from app.utils.storage import get_file_path
from app.adapters.factory import get_provider_status
from app.utils.ffmpeg_utils import ffmpeg_available

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health")
async def health_check():
    from app.core.database import _client
    db_ok = False
    try:
        await _client.admin.command("ping")
        db_ok = True
    except Exception:
        pass
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "ffmpeg": ffmpeg_available(),
        "providers": get_provider_status(),
    }


@router.get("/provider-status")
async def provider_status(user_id: str = Depends(get_current_user_id)):
    return get_provider_status()


@router.get("/download/{project_id}")
async def download_video(project_id: str, user_id: str = Depends(get_current_user_id)):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.video_url:
        raise HTTPException(status_code=404, detail="No video available")

    file_path = get_file_path(project.video_url)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    filename = f"{project.title.replace(' ', '_')[:50]}.mp4"
    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/download/{project_id}/subtitle")
async def download_subtitle(project_id: str, user_id: str = Depends(get_current_user_id)):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.subtitle_url:
        raise HTTPException(status_code=404, detail="No subtitle file available")

    file_path = get_file_path(project.subtitle_url)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Subtitle file not found")

    return FileResponse(
        path=str(file_path),
        media_type="text/srt",
        filename=f"{project.title[:50]}.srt",
    )
