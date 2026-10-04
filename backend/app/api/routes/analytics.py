from fastapi import APIRouter
from pydantic import BaseModel
from app.models.analytics import FeatureClick

router = APIRouter(prefix="/analytics", tags=["analytics"])

class FeatureClickRequest(BaseModel):
    feature_name: str

@router.post("/feature-click")
async def track_feature_click(request: FeatureClickRequest):
    click = FeatureClick(feature_name=request.feature_name)
    await click.insert()
    return {"status": "success", "message": "Click tracked"}
