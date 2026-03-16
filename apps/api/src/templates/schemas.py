from datetime import datetime
from enum import Enum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TemplateLocale = Literal["en", "fr"]


class FieldKind(str, Enum):
    SCALAR = "scalar"
    TABLE = "table"


class ScalarValueType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"


class TemplateFieldBase(BaseModel):
    key: Annotated[str, Field(min_length=1, max_length=100)]
    label: Annotated[str, Field(min_length=1, max_length=200)]
    required: bool = False
    description: str | None = None


class ScalarTemplateField(TemplateFieldBase):
    kind: Literal[FieldKind.SCALAR] = FieldKind.SCALAR
    value_type: ScalarValueType


class TableColumnDefinition(BaseModel):
    key: Annotated[str, Field(min_length=1, max_length=100)]
    label: Annotated[str, Field(min_length=1, max_length=200)]
    value_type: ScalarValueType
    required: bool = False
    description: str | None = None


class TableTemplateField(TemplateFieldBase):
    kind: Literal[FieldKind.TABLE] = FieldKind.TABLE
    columns: Annotated[list[TableColumnDefinition], Field(min_length=1)]
    min_rows: int = Field(default=0, ge=0)


TemplateField = Annotated[ScalarTemplateField | TableTemplateField, Field(discriminator="kind")]


class TemplateModule(BaseModel):
    key: Annotated[str, Field(min_length=1, max_length=100)]
    label: Annotated[str, Field(min_length=1, max_length=200)]
    fields: list[TemplateField] = Field(default_factory=list)


class TemplateBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    description: str | None = None
    locale: TemplateLocale
    modules: list[TemplateModule] = Field(default_factory=list)


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    description: str | None = None
    locale: TemplateLocale | None = None
    modules: list[TemplateModule] | None = None


class TemplateRead(TemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
