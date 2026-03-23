import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260317_000005"
down_revision = "20260317_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("document_category_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column(
            "classification_status",
            sa.String(length=32),
            nullable=False,
            server_default="unclassified",
        ),
    )
    op.add_column(
        "documents",
        sa.Column("classification_method", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column(
            "classification_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "documents",
        sa.Column("classified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_documents_document_category_id",
        "documents",
        "document_categories",
        ["document_category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_documents_document_category_id",
        "documents",
        ["document_category_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_documents_document_category_id", table_name="documents")
    op.drop_constraint("fk_documents_document_category_id", "documents", type_="foreignkey")
    op.drop_column("documents", "classified_at")
    op.drop_column("documents", "classification_metadata")
    op.drop_column("documents", "classification_method")
    op.drop_column("documents", "classification_status")
    op.drop_column("documents", "document_category_id")
