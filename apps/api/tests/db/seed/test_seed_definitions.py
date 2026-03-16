from uuid import UUID

from src.db.seed.document_categories import (
    DOCUMENT_CATEGORY_SEEDS,
    get_missing_document_category_seeds,
)
from src.db.seed.extraction_templates import (
    EXTRACTION_TEMPLATE_SEEDS,
    get_missing_extraction_template_seeds,
)


def test_document_category_seeds_have_unique_names() -> None:
    category_names = [seed.name for seed in DOCUMENT_CATEGORY_SEEDS]

    assert len(category_names) == len(set(category_names))
    assert "Loan Application" in category_names
    assert "Insurance Certificate" in category_names


def test_extraction_template_seeds_match_expected_starter_templates() -> None:
    template_ids = [str(seed.id) for seed in EXTRACTION_TEMPLATE_SEEDS]
    template_names = [seed.name for seed in EXTRACTION_TEMPLATE_SEEDS]

    assert template_ids == [
        "11111111-1111-4111-8111-111111111111",
        "22222222-2222-4222-8222-222222222222",
        "33333333-3333-4333-8333-333333333333",
        "44444444-4444-4444-8444-444444444444",
    ]
    assert template_names == [
        "Vendor Invoice",
        "Purchase Order",
        "Service Contract",
        "Facture Fournisseur",
    ]


def test_document_category_seed_filtering_skips_existing_names() -> None:
    missing_seeds = get_missing_document_category_seeds({"Identity Document", "Invoice"})

    missing_names = [seed.name for seed in missing_seeds]

    assert "Identity Document" not in missing_names
    assert "Invoice" not in missing_names
    assert "Loan Offer" in missing_names


def test_extraction_template_seed_filtering_skips_existing_ids_and_names() -> None:
    missing_seeds = get_missing_extraction_template_seeds(
        {
            UUID("11111111-1111-4111-8111-111111111111"),
            UUID("33333333-3333-4333-8333-333333333333"),
        },
        {"Facture Fournisseur"},
    )

    missing_names = [seed.name for seed in missing_seeds]

    assert missing_names == ["Purchase Order"]
