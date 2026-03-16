from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db_session
from src.extraction_templates.repository import ExtractionTemplateRepository
from src.extraction_templates.schemas import (
    ExtractionTemplateCreate,
    ExtractionTemplateRead,
    ExtractionTemplateUpdate,
)
from src.extraction_templates.service import ExtractionTemplateService

router = APIRouter(prefix="/api/extraction-templates", tags=["extraction-templates"])


def get_extraction_template_service(
    session: AsyncSession = Depends(get_async_db_session),
) -> ExtractionTemplateService:
    repository = ExtractionTemplateRepository(session)
    return ExtractionTemplateService(repository)


@router.get("", response_model=list[ExtractionTemplateRead])
async def list_extraction_templates(
    service: ExtractionTemplateService = Depends(get_extraction_template_service),
) -> list[ExtractionTemplateRead]:
    return await service.list_extraction_templates()


@router.post("", response_model=ExtractionTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_extraction_template(
    payload: ExtractionTemplateCreate,
    service: ExtractionTemplateService = Depends(get_extraction_template_service),
) -> ExtractionTemplateRead:
    return await service.create_extraction_template(payload)


@router.get("/{template_id}", response_model=ExtractionTemplateRead)
async def get_extraction_template(
    template_id: UUID,
    service: ExtractionTemplateService = Depends(get_extraction_template_service),
) -> ExtractionTemplateRead:
    return await service.get_extraction_template(template_id)


@router.patch("/{template_id}", response_model=ExtractionTemplateRead)
async def update_extraction_template(
    template_id: UUID,
    payload: ExtractionTemplateUpdate,
    service: ExtractionTemplateService = Depends(get_extraction_template_service),
) -> ExtractionTemplateRead:
    return await service.update_extraction_template(template_id, payload)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_extraction_template(
    template_id: UUID,
    service: ExtractionTemplateService = Depends(get_extraction_template_service),
) -> Response:
    await service.delete_extraction_template(template_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
