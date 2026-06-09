from fastapi import APIRouter, Depends

from app.api.deps import get_pipeline_service
from app.schemas.analytics import RefreshResponse
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_pipeline(service: PipelineService = Depends(get_pipeline_service)) -> RefreshResponse:
    await service.refresh()
    return RefreshResponse(refreshed=True, message="Analytics are computed on demand; cache refresh completed")

