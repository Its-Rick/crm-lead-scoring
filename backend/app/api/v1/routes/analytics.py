from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_call_insights_service, get_pipeline_service
from app.schemas.analytics import AccountAnalytics, CallInsightsResponse, PaginatedAccountAnalytics
from app.services.call_insights_service import CallInsightsService
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/accounts", response_model=PaginatedAccountAnalytics)
async def list_accounts(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    industry: str | None = None,
    account_status: str | None = None,
    service: PipelineService = Depends(get_pipeline_service),
) -> PaginatedAccountAnalytics:
    return await service.list_account_analytics(
        limit=limit,
        offset=offset,
        industry=industry,
        account_status=account_status,
    )


@router.get("/accounts/{account_id}", response_model=AccountAnalytics)
async def get_account(account_id: str, service: PipelineService = Depends(get_pipeline_service)) -> AccountAnalytics:
    account = await service.get_account_analytics(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.get("/lead-scores", response_model=PaginatedAccountAnalytics)
async def list_lead_scores(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None, pattern="^(Hot|Warm|Cold|hot|warm|cold)$"),
    industry: str | None = None,
    account_status: str | None = None,
    min_score: int | None = Query(default=None, ge=0, le=100),
    service: PipelineService = Depends(get_pipeline_service),
) -> PaginatedAccountAnalytics:
    return await service.list_lead_scores(
        limit=limit,
        offset=offset,
        category=category,
        industry=industry,
        account_status=account_status,
        min_score=min_score,
    )


@router.get("/call-insights", response_model=CallInsightsResponse)
async def get_call_insights(
    service: CallInsightsService = Depends(get_call_insights_service),
) -> CallInsightsResponse:
    return await service.get_insights()


@router.get("/follow-ups", response_model=PaginatedAccountAnalytics)
async def list_followups(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: PipelineService = Depends(get_pipeline_service),
) -> PaginatedAccountAnalytics:
    return await service.list_followups(limit=limit, offset=offset)

