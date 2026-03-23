import uuid
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from src.document_categories.model import DocumentCategoryModel

SEED_NAMESPACE = uuid.UUID("f6463df4-01ec-4f14-81c3-dbcb4b3643df")
DOCUMENT_CATEGORY_DEFINITIONS = [
    ("identity_document", "Identity Document"),
    ("proof_of_address", "Proof of Address"),
    ("bank_statement", "Bank Statement"),
    ("payslip", "Payslip"),
    ("tax_notice", "Tax Notice"),
    ("employment_contract", "Employment Contract"),
    ("purchase_agreement", "Purchase Agreement"),
    ("loan_application", "Loan Application"),
    ("loan_offer", "Loan Offer"),
    ("insurance_certificate", "Insurance Certificate"),
    ("property_valuation_report", "Property Valuation Report"),
    ("company_registration_extract", "Company Registration Extract"),
    ("invoice", "Invoice"),
    ("receipt", "Receipt"),
    ("purchase_order", "Purchase Order"),
    ("signed_contract", "Signed Contract"),
]


class DocumentCategorySeed(BaseModel):
    id: UUID
    name: Annotated[str, Field(min_length=1, max_length=120)]
    label_key: Annotated[str, Field(min_length=1, max_length=120)]


DOCUMENT_CATEGORY_SEEDS = [
    DocumentCategorySeed(
        id=uuid.uuid5(SEED_NAMESPACE, label_key),
        name=name,
        label_key=label_key,
    )
    for label_key, name in DOCUMENT_CATEGORY_DEFINITIONS
]


def get_missing_document_category_seeds(
    existing_label_keys: set[str],
) -> list[DocumentCategorySeed]:
    return [seed for seed in DOCUMENT_CATEGORY_SEEDS if seed.label_key not in existing_label_keys]


async def seed_document_categories(session: AsyncSession) -> int:
    existing_label_keys_result = await session.execute(select(DocumentCategoryModel.label_key))
    existing_label_keys = set(existing_label_keys_result.scalars().all())
    missing_seeds = get_missing_document_category_seeds(existing_label_keys)

    if not missing_seeds:
        return 0

    insert_statement = postgresql.insert(DocumentCategoryModel).values(
        [seed.model_dump(mode="python") for seed in missing_seeds]
    )
    await session.execute(
        insert_statement.on_conflict_do_nothing(index_elements=["label_key"])
    )
    return len(missing_seeds)
