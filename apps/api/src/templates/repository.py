from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.templates.model import TemplateModel
from src.templates.schemas import TemplateCreate, TemplateUpdate


class TemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[TemplateModel]:
        result = await self._session.execute(
            select(TemplateModel).order_by(TemplateModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, template_id: UUID) -> TemplateModel | None:
        result = await self._session.execute(
            select(TemplateModel).where(TemplateModel.id == template_id)
        )
        return result.scalar_one_or_none()

    async def create(self, payload: TemplateCreate) -> TemplateModel:
        template = TemplateModel(**payload.model_dump(mode="json"))
        self._session.add(template)
        await self._session.commit()
        await self._session.refresh(template)
        return template

    async def update(self, template: TemplateModel, payload: TemplateUpdate) -> TemplateModel:
        for field, value in payload.model_dump(exclude_unset=True, mode="json").items():
            setattr(template, field, value)

        await self._session.commit()
        await self._session.refresh(template)
        return template

    async def delete(self, template: TemplateModel) -> None:
        await self._session.delete(template)
        await self._session.commit()
