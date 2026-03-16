import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class DocumentModel(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(16), nullable=False)
    file_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(120), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    public_url: Mapped[str | None] = mapped_column(Text(), nullable=True)
    ingestion_status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    ingestion_phase: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    ingestion_error: Mapped[str | None] = mapped_column(Text(), nullable=True)
    content_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text(), nullable=True)
    extraction_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ocr_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ocr_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ocr_raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    document_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    classification_confidence: Mapped[float | None] = mapped_column(Float(), nullable=True)
    classification_rationale: Mapped[str | None] = mapped_column(Text(), nullable=True)
    detected_language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    authenticity_assessment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    suggested_normalized_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    chunks: Mapped[list["DocumentChunkModel"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunkModel.chunk_index",
    )
    ingestion_events: Mapped[list["DocumentIngestionEventModel"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentIngestionEventModel.sequence_number",
    )


class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer(), nullable=False)
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    embedding_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(120), nullable=False)
    embedding_dimensions: Mapped[int] = mapped_column(Integer(), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float()), nullable=False)
    document: Mapped[DocumentModel] = relationship(back_populates="chunks")


class DocumentIngestionEventModel(Base):
    __tablename__ = "document_ingestion_events"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "sequence_number",
            name="uq_document_ingestion_events_document_sequence",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_number: Mapped[int] = mapped_column(Integer(), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    phase: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    document: Mapped[DocumentModel] = relationship(back_populates="ingestion_events")
