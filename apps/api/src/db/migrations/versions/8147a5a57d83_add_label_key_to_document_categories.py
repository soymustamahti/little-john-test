"""add label key to document categories

Revision ID: 8147a5a57d83
Revises: 20260316_000002
Create Date: 2026-03-16 17:39:58.721171

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8147a5a57d83"
down_revision = "20260316_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_categories",
        sa.Column("label_key", sa.String(length=120), nullable=False),
    )
    op.create_unique_constraint(
        "uq_document_categories_label_key",
        "document_categories",
        ["label_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_document_categories_label_key",
        "document_categories",
        type_="unique",
    )
    op.drop_column("document_categories", "label_key")
