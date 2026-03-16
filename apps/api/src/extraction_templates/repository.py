from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.extraction_templates.model import ExtractionTemplateModel
from src.extraction_templates.schemas import ExtractionTemplateCreate, ExtractionTemplateUpdate


class ExtractionTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[ExtractionTemplateModel]:
        result = await self._session.execute(
            select(ExtractionTemplateModel).order_by(ExtractionTemplateModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, template_id: UUID) -> ExtractionTemplateModel | None:
        result = await self._session.execute(
            select(ExtractionTemplateModel).where(ExtractionTemplateModel.id == template_id)
        )
        return result.scalar_one_or_none()

    async def create(self, payload: ExtractionTemplateCreate) -> ExtractionTemplateModel:
        template = ExtractionTemplateModel(**payload.model_dump(mode="json"))
        self._session.add(template)
        await self._session.commit()
        await self._session.refresh(template)
        return template

    async def update(
        self,
        template: ExtractionTemplateModel,
        payload: ExtractionTemplateUpdate,
    ) -> ExtractionTemplateModel:
        for field, value in payload.model_dump(exclude_unset=True, mode="json").items():
            setattr(template, field, value)

        await self._session.commit()
        await self._session.refresh(template)
        return template

    async def delete(self, template: ExtractionTemplateModel) -> None:
        await self._session.delete(template)
        await self._session.commit()
