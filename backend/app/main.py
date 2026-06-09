from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import get_session
from app.repositories.crm_repository import CRMRepository
from app.schemas.analytics import HealthResponse

settings = get_settings()
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Explainable AI analytics APIs for CRM lead scoring, call insights, and follow-up recommendations.",
)
app.include_router(api_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    database = "ok"
    try:
        await CRMRepository(session).ping()
    except Exception:
        database = "unavailable"
    return HealthResponse(service="ok", database=database, version=settings.app_version)
