from uuid import UUID

from fastapi import HTTPException, status

from src.extraction_templates.repository import ExtractionTemplateRepository
from src.extraction_templates.schemas import (
    ExtractionTemplateCreate,
    ExtractionTemplateRead,
    ExtractionTemplateUpdate,
)


class ExtractionTemplateService:
    def __init__(self, repository: ExtractionTemplateRepository) -> None:
        self._repository = repository

    async def list_extraction_templates(self) -> list[ExtractionTemplateRead]:
        templates = await self._repository.list()
        return [ExtractionTemplateRead.model_validate(template) for template in templates]

    async def get_extraction_template(self, template_id: UUID) -> ExtractionTemplateRead:
        template = await self._repository.get(template_id)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction template {template_id} was not found.",
            )
        return ExtractionTemplateRead.model_validate(template)

    async def create_extraction_template(
        self,
        payload: ExtractionTemplateCreate,
    ) -> ExtractionTemplateRead:
        template = await self._repository.create(payload)
        return ExtractionTemplateRead.model_validate(template)

    async def update_extraction_template(
        self,
        template_id: UUID,
        payload: ExtractionTemplateUpdate,
    ) -> ExtractionTemplateRead:
        template = await self._repository.get(template_id)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction template {template_id} was not found.",
            )
        updated_template = await self._repository.update(template, payload)
        return ExtractionTemplateRead.model_validate(updated_template)

    async def delete_extraction_template(self, template_id: UUID) -> None:
        template = await self._repository.get(template_id)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction template {template_id} was not found.",
            )
        await self._repository.delete(template)
