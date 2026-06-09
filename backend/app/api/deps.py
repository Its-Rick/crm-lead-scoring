from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.repositories.crm_repository import CRMRepository
from app.services.call_insights_service import CallInsightsService
from app.services.pipeline_service import PipelineService


async def get_repository(session: AsyncSession = Depends(get_session)) -> AsyncGenerator[CRMRepository, None]:
    yield CRMRepository(session)


async def get_pipeline_service(session: AsyncSession = Depends(get_session)) -> AsyncGenerator[PipelineService, None]:
    yield PipelineService(CRMRepository(session))


async def get_call_insights_service(session: AsyncSession = Depends(get_session)) -> AsyncGenerator[CallInsightsService, None]:
    yield CallInsightsService(CRMRepository(session))
