import asyncio
import logging
from uuid import UUID

from sqlalchemy import select

from src.core.database import get_async_session_factory
from src.db.migration_runner import run_app_migrations
from src.templates.model import TemplateModel

LOGGER = logging.getLogger(__name__)

SEEDED_TEMPLATES: list[dict[str, object]] = [
    {
        "id": UUID("11111111-1111-4111-8111-111111111111"),
        "name": "Vendor Invoice",
        "description": (
            "Comprehensive invoice template for vendor bills, including payment terms and "
            "line-item reconciliation."
        ),
        "locale": "en",
        "modules": [
            {
                "key": "vendor_information",
                "label": "Vendor Information",
                "fields": [
                    {
                        "key": "vendor_name",
                        "label": "Vendor Name",
                        "required": True,
                        "description": "Legal or trading name of the issuer.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "vendor_tax_id",
                        "label": "Vendor Tax ID",
                        "required": False,
                        "description": "VAT, EIN, or equivalent fiscal identifier.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "vendor_address",
                        "label": "Vendor Address",
                        "required": False,
                        "description": "Full billing or remit-to address.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                ],
            },
            {
                "key": "invoice_overview",
                "label": "Invoice Overview",
                "fields": [
                    {
                        "key": "invoice_number",
                        "label": "Invoice Number",
                        "required": True,
                        "description": "Supplier invoice reference.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "invoice_date",
                        "label": "Invoice Date",
                        "required": True,
                        "description": "Document issue date.",
                        "kind": "scalar",
                        "value_type": "date",
                    },
                    {
                        "key": "due_date",
                        "label": "Due Date",
                        "required": False,
                        "description": "Payment deadline on the document.",
                        "kind": "scalar",
                        "value_type": "date",
                    },
                    {
                        "key": "currency",
                        "label": "Currency",
                        "required": True,
                        "description": "Invoice currency code or symbol.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "purchase_order_number",
                        "label": "Purchase Order Number",
                        "required": False,
                        "description": "PO or engagement reference cited by the vendor.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                ],
            },
            {
                "key": "payment_summary",
                "label": "Payment Summary",
                "fields": [
                    {
                        "key": "subtotal_amount",
                        "label": "Subtotal Amount",
                        "required": True,
                        "description": "Amount before taxes and discounts.",
                        "kind": "scalar",
                        "value_type": "number",
                    },
                    {
                        "key": "tax_amount",
                        "label": "Tax Amount",
                        "required": False,
                        "description": "Total tax or VAT amount.",
                        "kind": "scalar",
                        "value_type": "number",
                    },
                    {
                        "key": "total_amount",
                        "label": "Total Amount",
                        "required": True,
                        "description": "Final amount payable.",
                        "kind": "scalar",
                        "value_type": "number",
                    },
                    {
                        "key": "payment_terms",
                        "label": "Payment Terms",
                        "required": False,
                        "description": "Terms such as Net 30 or immediate transfer.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "iban",
                        "label": "IBAN / Bank Account",
                        "required": False,
                        "description": "Payment destination account when available.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                ],
            },
            {
                "key": "line_items",
                "label": "Line Items",
                "fields": [
                    {
                        "key": "invoice_items",
                        "label": "Invoice Items",
                        "required": False,
                        "description": "Products or services billed on the invoice.",
                        "kind": "table",
                        "min_rows": 1,
                        "columns": [
                            {
                                "key": "description",
                                "label": "Description",
                                "value_type": "string",
                                "required": True,
                                "description": "Line item narrative.",
                            },
                            {
                                "key": "quantity",
                                "label": "Quantity",
                                "value_type": "number",
                                "required": False,
                                "description": "Billed quantity.",
                            },
                            {
                                "key": "unit_price",
                                "label": "Unit Price",
                                "value_type": "number",
                                "required": False,
                                "description": "Price per unit.",
                            },
                            {
                                "key": "line_total",
                                "label": "Line Total",
                                "value_type": "number",
                                "required": True,
                                "description": "Total amount for the row.",
                            },
                            {
                                "key": "tax_rate",
                                "label": "Tax Rate",
                                "value_type": "number",
                                "required": False,
                                "description": "Applied tax percentage when present.",
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "id": UUID("22222222-2222-4222-8222-222222222222"),
        "name": "Purchase Order",
        "description": (
            "Procurement-ready purchase order template covering supplier, buyer, logistics, "
            "and ordered items."
        ),
        "locale": "en",
        "modules": [
            {
                "key": "buyer_information",
                "label": "Buyer Information",
                "fields": [
                    {
                        "key": "buyer_name",
                        "label": "Buyer Name",
                        "required": True,
                        "description": "Company or entity placing the order.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "buyer_email",
                        "label": "Buyer Email",
                        "required": False,
                        "description": "Operational contact for the order.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "ship_to_address",
                        "label": "Ship-To Address",
                        "required": False,
                        "description": "Final destination for the goods.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                ],
            },
            {
                "key": "supplier_information",
                "label": "Supplier Information",
                "fields": [
                    {
                        "key": "supplier_name",
                        "label": "Supplier Name",
                        "required": True,
                        "description": "Vendor fulfilling the purchase order.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "supplier_contact",
                        "label": "Supplier Contact",
                        "required": False,
                        "description": "Buyer-side visible account contact.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "supplier_address",
                        "label": "Supplier Address",
                        "required": False,
                        "description": "Registered or shipping origin address.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                ],
            },
            {
                "key": "order_terms",
                "label": "Order Terms",
                "fields": [
                    {
                        "key": "po_number",
                        "label": "PO Number",
                        "required": True,
                        "description": "Primary procurement identifier.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "issue_date",
                        "label": "Issue Date",
                        "required": True,
                        "description": "Purchase order creation date.",
                        "kind": "scalar",
                        "value_type": "date",
                    },
                    {
                        "key": "delivery_date",
                        "label": "Requested Delivery Date",
                        "required": False,
                        "description": "Requested delivery or fulfilment date.",
                        "kind": "scalar",
                        "value_type": "date",
                    },
                    {
                        "key": "currency",
                        "label": "Currency",
                        "required": True,
                        "description": "Commercial currency for the order.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "approved",
                        "label": "Approved",
                        "required": False,
                        "description": "Boolean flag indicating formal approval.",
                        "kind": "scalar",
                        "value_type": "boolean",
                    },
                    {
                        "key": "payment_terms",
                        "label": "Payment Terms",
                        "required": False,
                        "description": "Commercial payment conditions.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                ],
            },
            {
                "key": "ordered_items",
                "label": "Ordered Items",
                "fields": [
                    {
                        "key": "po_items",
                        "label": "PO Items",
                        "required": False,
                        "description": "Detailed list of requested products or services.",
                        "kind": "table",
                        "min_rows": 1,
                        "columns": [
                            {
                                "key": "sku",
                                "label": "SKU",
                                "value_type": "string",
                                "required": False,
                                "description": "Internal or supplier stock keeping unit.",
                            },
                            {
                                "key": "description",
                                "label": "Description",
                                "value_type": "string",
                                "required": True,
                                "description": "Requested item description.",
                            },
                            {
                                "key": "quantity",
                                "label": "Quantity",
                                "value_type": "number",
                                "required": True,
                                "description": "Requested quantity.",
                            },
                            {
                                "key": "unit_price",
                                "label": "Unit Price",
                                "value_type": "number",
                                "required": True,
                                "description": "Agreed price per unit.",
                            },
                            {
                                "key": "requested_delivery_date",
                                "label": "Requested Delivery Date",
                                "value_type": "date",
                                "required": False,
                                "description": "Row-specific delivery date when present.",
                            },
                            {
                                "key": "line_total",
                                "label": "Line Total",
                                "value_type": "number",
                                "required": True,
                                "description": "Computed or stated line amount.",
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "id": UUID("33333333-3333-4333-8333-333333333333"),
        "name": "Service Contract",
        "description": (
            "Long-form contract template for agreement metadata, dates, commercials, and "
            "deliverable milestones."
        ),
        "locale": "en",
        "modules": [
            {
                "key": "parties",
                "label": "Parties",
                "fields": [
                    {
                        "key": "client_name",
                        "label": "Client Name",
                        "required": True,
                        "description": "Entity purchasing the service.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "provider_name",
                        "label": "Provider Name",
                        "required": True,
                        "description": "Entity delivering the service.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "contract_number",
                        "label": "Contract Number",
                        "required": True,
                        "description": "Agreement reference number.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                ],
            },
            {
                "key": "agreement_dates",
                "label": "Agreement Dates",
                "fields": [
                    {
                        "key": "effective_date",
                        "label": "Effective Date",
                        "required": True,
                        "description": "Date the agreement comes into force.",
                        "kind": "scalar",
                        "value_type": "date",
                    },
                    {
                        "key": "termination_date",
                        "label": "Termination Date",
                        "required": False,
                        "description": "Contract end date if defined.",
                        "kind": "scalar",
                        "value_type": "date",
                    },
                    {
                        "key": "auto_renewal",
                        "label": "Auto Renewal",
                        "required": False,
                        "description": "Whether the contract renews automatically.",
                        "kind": "scalar",
                        "value_type": "boolean",
                    },
                    {
                        "key": "notice_period_days",
                        "label": "Notice Period (Days)",
                        "required": False,
                        "description": "Cancellation notice period expressed in days.",
                        "kind": "scalar",
                        "value_type": "number",
                    },
                ],
            },
            {
                "key": "commercial_terms",
                "label": "Commercial Terms",
                "fields": [
                    {
                        "key": "currency",
                        "label": "Currency",
                        "required": True,
                        "description": "Contract billing currency.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "billing_frequency",
                        "label": "Billing Frequency",
                        "required": False,
                        "description": "Monthly, quarterly, yearly, or milestone-based.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "contract_value",
                        "label": "Contract Value",
                        "required": False,
                        "description": "Total value of the agreement when explicit.",
                        "kind": "scalar",
                        "value_type": "number",
                    },
                    {
                        "key": "governing_law",
                        "label": "Governing Law",
                        "required": False,
                        "description": "Jurisdiction governing the agreement.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                ],
            },
            {
                "key": "milestones",
                "label": "Milestones",
                "fields": [
                    {
                        "key": "deliverables",
                        "label": "Deliverables",
                        "required": False,
                        "description": "Project milestones or acceptance checkpoints.",
                        "kind": "table",
                        "min_rows": 0,
                        "columns": [
                            {
                                "key": "deliverable",
                                "label": "Deliverable",
                                "value_type": "string",
                                "required": True,
                                "description": "Milestone or deliverable name.",
                            },
                            {
                                "key": "due_date",
                                "label": "Due Date",
                                "value_type": "date",
                                "required": False,
                                "description": "Scheduled completion date.",
                            },
                            {
                                "key": "amount",
                                "label": "Amount",
                                "value_type": "number",
                                "required": False,
                                "description": "Commercial amount tied to the milestone.",
                            },
                            {
                                "key": "acceptance_required",
                                "label": "Acceptance Required",
                                "value_type": "boolean",
                                "required": False,
                                "description": "Whether formal approval is required.",
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "id": UUID("44444444-4444-4444-8444-444444444444"),
        "name": "Facture Fournisseur",
        "description": (
            "Modele francophone de facture fournisseur avec resume fiscal et lignes de "
            "facturation detaillees."
        ),
        "locale": "fr",
        "modules": [
            {
                "key": "fournisseur",
                "label": "Fournisseur",
                "fields": [
                    {
                        "key": "nom_fournisseur",
                        "label": "Nom du fournisseur",
                        "required": True,
                        "description": "Raison sociale du fournisseur.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "siret",
                        "label": "SIRET",
                        "required": False,
                        "description": "Identifiant legal du fournisseur.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "adresse_fournisseur",
                        "label": "Adresse du fournisseur",
                        "required": False,
                        "description": "Adresse de facturation ou de siege.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                ],
            },
            {
                "key": "facture",
                "label": "Facture",
                "fields": [
                    {
                        "key": "numero_facture",
                        "label": "Numero de facture",
                        "required": True,
                        "description": "Reference principale de la facture.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                    {
                        "key": "date_facture",
                        "label": "Date de facture",
                        "required": True,
                        "description": "Date d'emission du document.",
                        "kind": "scalar",
                        "value_type": "date",
                    },
                    {
                        "key": "date_echeance",
                        "label": "Date d'echeance",
                        "required": False,
                        "description": "Date limite de paiement.",
                        "kind": "scalar",
                        "value_type": "date",
                    },
                    {
                        "key": "devise",
                        "label": "Devise",
                        "required": True,
                        "description": "Code devise ou symbole.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                ],
            },
            {
                "key": "resume_paiement",
                "label": "Resume Paiement",
                "fields": [
                    {
                        "key": "montant_ht",
                        "label": "Montant HT",
                        "required": True,
                        "description": "Montant hors taxes.",
                        "kind": "scalar",
                        "value_type": "number",
                    },
                    {
                        "key": "montant_tva",
                        "label": "Montant TVA",
                        "required": False,
                        "description": "Montant total de TVA.",
                        "kind": "scalar",
                        "value_type": "number",
                    },
                    {
                        "key": "montant_ttc",
                        "label": "Montant TTC",
                        "required": True,
                        "description": "Montant total toutes taxes comprises.",
                        "kind": "scalar",
                        "value_type": "number",
                    },
                    {
                        "key": "conditions_paiement",
                        "label": "Conditions de paiement",
                        "required": False,
                        "description": "Modalites de paiement mentionnees sur la facture.",
                        "kind": "scalar",
                        "value_type": "string",
                    },
                ],
            },
            {
                "key": "lignes",
                "label": "Lignes",
                "fields": [
                    {
                        "key": "lignes_facture",
                        "label": "Lignes de facture",
                        "required": False,
                        "description": "Prestations ou produits detailles sur la facture.",
                        "kind": "table",
                        "min_rows": 1,
                        "columns": [
                            {
                                "key": "description",
                                "label": "Description",
                                "value_type": "string",
                                "required": True,
                                "description": "Libelle de la ligne.",
                            },
                            {
                                "key": "quantite",
                                "label": "Quantite",
                                "value_type": "number",
                                "required": False,
                                "description": "Quantite facturée.",
                            },
                            {
                                "key": "prix_unitaire",
                                "label": "Prix unitaire",
                                "value_type": "number",
                                "required": False,
                                "description": "Prix unitaire de la ligne.",
                            },
                            {
                                "key": "montant_ligne",
                                "label": "Montant ligne",
                                "value_type": "number",
                                "required": True,
                                "description": "Montant total de la ligne.",
                            },
                        ],
                    }
                ],
            },
        ],
    },
]


async def seed_templates() -> None:
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        for template_payload in SEEDED_TEMPLATES:
            template_id = template_payload["id"]
            result = await session.execute(
                select(TemplateModel).where(TemplateModel.id == template_id)
            )
            existing = result.scalar_one_or_none()

            if existing is None:
                session.add(TemplateModel(**template_payload))
                LOGGER.info("Inserted template seed %s", template_payload["name"])
                continue

            existing.name = str(template_payload["name"])
            existing.description = template_payload["description"]
            existing.locale = str(template_payload["locale"])
            existing.modules = list(template_payload["modules"])
            LOGGER.info("Updated template seed %s", template_payload["name"])

        await session.commit()


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_app_migrations()
    await seed_templates()
    LOGGER.info("Template seeding completed.")


if __name__ == "__main__":
    asyncio.run(main())
