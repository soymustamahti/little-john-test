from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentCategoryBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=120)]


class DocumentCategoryCreate(DocumentCategoryBase):
    pass


class DocumentCategoryUpdate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=120)] | None = None


class DocumentCategoryRead(DocumentCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
