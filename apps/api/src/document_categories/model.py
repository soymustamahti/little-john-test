from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.documents.model import DocumentModel


class DocumentCategoryModel(Base):
    __tablename__ = "document_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    label_key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    documents: Mapped[list["DocumentModel"]] = relationship(back_populates="document_category")
