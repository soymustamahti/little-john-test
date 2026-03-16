import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260316_000004"
down_revision = "20260316_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "ingestion_status",
            sa.String(length=32),
            nullable=False,
            server_default="queued",
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "ingestion_phase",
            sa.String(length=32),
            nullable=False,
            server_default="uploaded",
        ),
    )
    op.add_column("documents", sa.Column("ingestion_error", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("content_source", sa.String(length=32), nullable=True))
    op.add_column("documents", sa.Column("extracted_text", sa.Text(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("extraction_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("documents", sa.Column("ocr_provider", sa.String(length=64), nullable=True))
    op.add_column("documents", sa.Column("ocr_model", sa.String(length=120), nullable=True))
    op.add_column(
        "documents",
        sa.Column("ocr_raw_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("document_category_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("documents", sa.Column("classification_confidence", sa.Float(), nullable=True))
    op.add_column("documents", sa.Column("classification_rationale", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("detected_language", sa.String(length=32), nullable=True))
    op.add_column(
        "documents",
        sa.Column("authenticity_assessment", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("suggested_normalized_filename", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_documents_sha256", "documents", ["sha256"], unique=False)
    op.create_index(
        "ix_documents_ingestion_status",
        "documents",
        ["ingestion_status"],
        unique=False,
    )
    op.create_index(
        "ix_documents_document_category_id",
        "documents",
        ["document_category_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_documents_document_category_id",
        "documents",
        "document_categories",
        ["document_category_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "chunk_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("embedding_provider", sa.String(length=64), nullable=False),
        sa.Column("embedding_model", sa.String(length=120), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunks_document_index",
        ),
    )
    op.create_index(
        "ix_document_chunks_document_id",
        "document_chunks",
        ["document_id"],
        unique=False,
    )

    op.create_table(
        "document_ingestion_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("phase", sa.String(length=32), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "sequence_number",
            name="uq_document_ingestion_events_document_sequence",
        ),
    )
    op.create_index(
        "ix_document_ingestion_events_document_id",
        "document_ingestion_events",
        ["document_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_ingestion_events_document_id",
        table_name="document_ingestion_events",
    )
    op.drop_table("document_ingestion_events")

    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_constraint("fk_documents_document_category_id", "documents", type_="foreignkey")
    op.drop_index("ix_documents_document_category_id", table_name="documents")
    op.drop_index("ix_documents_ingestion_status", table_name="documents")
    op.drop_index("ix_documents_sha256", table_name="documents")

    op.drop_column("documents", "processing_completed_at")
    op.drop_column("documents", "processing_started_at")
    op.drop_column("documents", "suggested_normalized_filename")
    op.drop_column("documents", "authenticity_assessment")
    op.drop_column("documents", "detected_language")
    op.drop_column("documents", "classification_rationale")
    op.drop_column("documents", "classification_confidence")
    op.drop_column("documents", "document_category_id")
    op.drop_column("documents", "ocr_raw_response")
    op.drop_column("documents", "ocr_model")
    op.drop_column("documents", "ocr_provider")
    op.drop_column("documents", "extraction_metadata")
    op.drop_column("documents", "extracted_text")
    op.drop_column("documents", "content_source")
    op.drop_column("documents", "ingestion_error")
    op.drop_column("documents", "ingestion_phase")
    op.drop_column("documents", "ingestion_status")
