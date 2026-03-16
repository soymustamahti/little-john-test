from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from src.extraction_templates.schemas import (
    ExtractionTemplateCreate,
    ExtractionTemplateUpdate,
    ScalarTemplateField,
    ScalarValueType,
    TemplateModule,
)
from src.extraction_templates.service import ExtractionTemplateService


@dataclass
class FakeExtractionTemplateRecord:
    id: UUID
    name: str
    description: str | None
    locale: str
    modules: list[dict[str, object]]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class FakeExtractionTemplateRepository:
    def __init__(self) -> None:
        self._records: dict[UUID, FakeExtractionTemplateRecord] = {}

    async def list(self) -> list[FakeExtractionTemplateRecord]:
        return sorted(self._records.values(), key=lambda record: record.created_at, reverse=True)

    async def get(self, template_id: UUID) -> FakeExtractionTemplateRecord | None:
        return self._records.get(template_id)

    async def create(self, payload: ExtractionTemplateCreate) -> FakeExtractionTemplateRecord:
        record = FakeExtractionTemplateRecord(id=uuid4(), **payload.model_dump(mode="json"))
        self._records[record.id] = record
        return record

    async def update(
        self,
        template: FakeExtractionTemplateRecord,
        payload: ExtractionTemplateUpdate,
    ) -> FakeExtractionTemplateRecord:
        for field_name, value in payload.model_dump(exclude_unset=True, mode="json").items():
            setattr(template, field_name, value)
        template.updated_at = datetime.now(UTC)
        return template

    async def delete(self, template: FakeExtractionTemplateRecord) -> None:
        self._records.pop(template.id, None)


def build_template_payload(name: str = "Invoice extraction") -> ExtractionTemplateCreate:
    return ExtractionTemplateCreate(
        name=name,
        description="Extract invoice header fields",
        locale="en",
        modules=[
            TemplateModule(
                key="header",
                label="Header",
                fields=[
                    ScalarTemplateField(
                        key="invoice_number",
                        label="Invoice Number",
                        value_type=ScalarValueType.STRING,
                        required=True,
                    )
                ],
            )
        ],
    )


@pytest.mark.asyncio
async def test_create_extraction_template_returns_serialized_template() -> None:
    service = ExtractionTemplateService(FakeExtractionTemplateRepository())

    created_template = await service.create_extraction_template(build_template_payload())

    assert created_template.name == "Invoice extraction"
    assert created_template.modules[0].fields[0].key == "invoice_number"


@pytest.mark.asyncio
async def test_get_extraction_template_raises_404_for_unknown_id() -> None:
    service = ExtractionTemplateService(FakeExtractionTemplateRepository())

    with pytest.raises(HTTPException) as exc_info:
        await service.get_extraction_template(uuid4())

    assert exc_info.value.status_code == 404
    assert "Extraction template" in exc_info.value.detail
