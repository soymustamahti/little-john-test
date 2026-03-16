from uuid import UUID

from fastapi import HTTPException, status

from src.templates.repository import TemplateRepository
from src.templates.schemas import TemplateCreate, TemplateRead, TemplateUpdate


class TemplateService:
    def __init__(self, repository: TemplateRepository) -> None:
        self._repository = repository

    async def list_templates(self) -> list[TemplateRead]:
        templates = await self._repository.list()
        return [TemplateRead.model_validate(template) for template in templates]

    async def get_template(self, template_id: UUID) -> TemplateRead:
        template = await self._repository.get(template_id)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_id} was not found.",
            )
        return TemplateRead.model_validate(template)

    async def create_template(self, payload: TemplateCreate) -> TemplateRead:
        template = await self._repository.create(payload)
        return TemplateRead.model_validate(template)

    async def update_template(self, template_id: UUID, payload: TemplateUpdate) -> TemplateRead:
        template = await self._repository.get(template_id)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_id} was not found.",
            )
        updated_template = await self._repository.update(template, payload)
        return TemplateRead.model_validate(updated_template)

    async def delete_template(self, template_id: UUID) -> None:
        template = await self._repository.get(template_id)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_id} was not found.",
            )
        await self._repository.delete(template)
