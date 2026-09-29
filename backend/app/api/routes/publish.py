"""
Publishing routes — honest Qoneqt integration.
If no Qoneqt API key is configured, returns a manual publishing workflow.
Does NOT claim publication unless a real confirmed API response is received.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from app.models.project import Project
from app.models.publish import PublishRecord, PublishStatus
from app.schemas.job import PublishRequest, PublishResponse
from app.core.security import get_current_user_id
from app.core.config import settings
from loguru import logger

router = APIRouter(prefix="/publish", tags=["Publishing"])


@router.post("/{project_id}", response_model=PublishResponse)
async def publish_project(
    project_id: str,
    data: PublishRequest,
    user_id: str = Depends(get_current_user_id),
):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.video_url:
        raise HTTPException(status_code=400, detail="No video available. Render the video first.")

    record = PublishRecord(
        project_id=project_id,
        owner_id=user_id,
        title=data.title or project.video_title or project.title,
        description=data.description or project.video_description,
        hashtags=data.hashtags or project.hashtags,
        video_url=project.video_url,
    )

    if settings.has_qoneqt_api:
        # Real API integration (implement when official API is available)
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.QONEQT_API_URL}/videos",
                    json={
                        "title": record.title,
                        "description": record.description,
                        "hashtags": record.hashtags,
                        "video_url": project.video_url,
                    },
                    headers={"Authorization": f"Bearer {settings.QONEQT_API_KEY}"},
                    timeout=30,
                )
                resp.raise_for_status()
                result = resp.json()
                record.status = PublishStatus.PUBLISHED
                record.external_post_id = result.get("id")
                record.published_at = datetime.utcnow()
                await record.save()
                return PublishResponse(
                    id=str(record.id),
                    project_id=project_id,
                    status="published",
                    platform="qoneqt",
                    manual_workflow=False,
                    message="Video published to Qoneqt successfully!",
                )
        except Exception as e:
            logger.error(f"Qoneqt API publish failed: {e}")
            record.status = PublishStatus.FAILED
            record.error_message = str(e)
            await record.save()
            raise HTTPException(status_code=502, detail=f"Qoneqt API error: {str(e)}")
    else:
        # Manual publishing workflow — honest, no fake publish
        record.status = PublishStatus.MANUAL
        await record.save()
        hashtag_string = " ".join(data.hashtags or project.hashtags)
        caption = f"{data.title or project.video_title}\n\n{data.description or project.video_description}\n\n{hashtag_string}"
        return PublishResponse(
            id=str(record.id),
            project_id=project_id,
            status="manual",
            platform="qoneqt",
            manual_workflow=True,
            qoneqt_url=settings.QONEQT_APP_URL,
            message=(
                "⚠️ MANUAL PUBLISHING WORKFLOW: "
                "No Qoneqt API integration is configured. "
                "Download your video, copy the caption below, open Qoneqt, and post manually."
            ),
        )


@router.get("/{project_id}")
async def get_publish_records(project_id: str, user_id: str = Depends(get_current_user_id)):
    project = await Project.get(project_id)
    if not project or str(project.owner_id) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    records = await PublishRecord.find({"project_id": project_id}).sort("-created_at").to_list()
    return [
        {
            "id": str(r.id),
            "status": r.status,
            "platform": r.platform,
            "title": r.title,
            "created_at": r.created_at,
            "published_at": r.published_at,
        }
        for r in records
    ]
