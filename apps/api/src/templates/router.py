from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db_session
from src.templates.repository import TemplateRepository
from src.templates.schemas import TemplateCreate, TemplateRead, TemplateUpdate
from src.templates.service import TemplateService

router = APIRouter(prefix="/api/templates", tags=["templates"])


def get_template_service(
    session: AsyncSession = Depends(get_async_db_session),
) -> TemplateService:
    repository = TemplateRepository(session)
    return TemplateService(repository)


@router.get("", response_model=list[TemplateRead])
async def list_templates(
    service: TemplateService = Depends(get_template_service),
) -> list[TemplateRead]:
    return await service.list_templates()


@router.post("", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: TemplateCreate,
    service: TemplateService = Depends(get_template_service),
) -> TemplateRead:
    return await service.create_template(payload)


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: UUID,
    service: TemplateService = Depends(get_template_service),
) -> TemplateRead:
    return await service.get_template(template_id)


@router.patch("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: UUID,
    payload: TemplateUpdate,
    service: TemplateService = Depends(get_template_service),
) -> TemplateRead:
    return await service.update_template(template_id, payload)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    service: TemplateService = Depends(get_template_service),
) -> Response:
    await service.delete_template(template_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
