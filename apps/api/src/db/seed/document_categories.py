import uuid
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from src.document_categories.model import DocumentCategoryModel

SEED_NAMESPACE = uuid.UUID("f6463df4-01ec-4f14-81c3-dbcb4b3643df")
DOCUMENT_CATEGORY_NAMES = [
    "Identity Document",
    "Proof of Address",
    "Bank Statement",
    "Payslip",
    "Tax Notice",
    "Employment Contract",
    "Purchase Agreement",
    "Loan Application",
    "Loan Offer",
    "Insurance Certificate",
    "Property Valuation Report",
    "Company Registration Extract",
    "Invoice",
    "Receipt",
    "Purchase Order",
    "Signed Contract",
]


class DocumentCategorySeed(BaseModel):
    id: UUID
    name: Annotated[str, Field(min_length=1, max_length=120)]


DOCUMENT_CATEGORY_SEEDS = [
    DocumentCategorySeed(id=uuid.uuid5(SEED_NAMESPACE, name), name=name)
    for name in DOCUMENT_CATEGORY_NAMES
]


def get_missing_document_category_seeds(
    existing_names: set[str],
) -> list[DocumentCategorySeed]:
    return [seed for seed in DOCUMENT_CATEGORY_SEEDS if seed.name not in existing_names]


async def seed_document_categories(session: AsyncSession) -> int:
    existing_names_result = await session.execute(select(DocumentCategoryModel.name))
    existing_names = set(existing_names_result.scalars().all())
    missing_seeds = get_missing_document_category_seeds(existing_names)

    if not missing_seeds:
        return 0

    insert_statement = postgresql.insert(DocumentCategoryModel).values(
        [seed.model_dump(mode="python") for seed in missing_seeds]
    )
    await session.execute(insert_statement.on_conflict_do_nothing(index_elements=["name"]))
    return len(missing_seeds)
