import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260316_000002"
down_revision = "20260316_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("templates", "extraction_templates")

    op.create_table(
        "document_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )


def downgrade() -> None:
    op.drop_table("document_categories")
    op.rename_table("extraction_templates", "templates")
