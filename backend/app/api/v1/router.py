from fastapi import APIRouter

from app.api.v1.routes.analytics import router as analytics_router
from app.api.v1.routes.pipeline import router as pipeline_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(analytics_router)
api_router.include_router(pipeline_router)

