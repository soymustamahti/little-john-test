# API

The backend is an [Aegra](https://github.com/ibbybuilds/aegra) project that hosts a LangGraph
agent.

## Common Commands

Run these from the repo root:

```bash
pnpm api:deps
pnpm dev:api
pnpm build:api
pnpm lint:api
pnpm typecheck:api
pnpm docker:up
pnpm docker:down
```

Or run the package scripts directly from `apps/api/`:

```bash
pnpm dev
pnpm build
pnpm lint
pnpm typecheck
```

## Files

- `aegra.json`: graph registration for Aegra
- `pyproject.toml`: Python dependencies and tooling
- `src/main.py`: global FastAPI app mounted by Aegra
- `src/agents/extract_agent/graph.py`: current LangGraph definition
- `src/extraction_templates/`: extraction template feature slice with CRUD
- `src/document_categories/`: document category feature slice with CRUD
- `src/db/`: shared database base and global custom Alembic environment
- `src/db/seed/`: idempotent reference data seeds applied after migrations
- `docker-compose.yml`: local PostgreSQL + API stack

## Aegra Integration Notes

- `http.app` is loaded as the module `src.main:app` because Aegra supports module imports for
  custom FastAPI apps and this avoids fragile file-path import behavior.
- Graphs remain file-based in `aegra.json`, which matches how Aegra loads graph exports.
- Avoid adding a root `alembic.ini` in `apps/api` unless you intentionally want to override
  Aegra's own migration chain.

## Extraction Templates

The extraction template feature is implemented as a self-contained slice under
`src/extraction_templates/`:

- `model.py`: SQLAlchemy template model
- `schemas.py`: request and response contracts
- `repository.py`: persistence access
- `service.py`: CRUD business logic
- `router.py`: FastAPI endpoints

Available endpoints:

- `GET /api/extraction-templates`
- `POST /api/extraction-templates`
- `GET /api/extraction-templates/{template_id}`
- `PATCH /api/extraction-templates/{template_id}`
- `DELETE /api/extraction-templates/{template_id}`

Default extraction template seeds are defined in `src/db/seed/extraction_templates.py` and
currently include:

- `Vendor Invoice`
- `Purchase Order`
- `Service Contract`
- `Facture Fournisseur`

## Document Categories

The document category feature is implemented as a parallel slice under `src/document_categories/`.
It stores the predefined document types that later classification will map uploaded files onto.

Available endpoints:

- `GET /api/document-categories`
- `POST /api/document-categories`
- `GET /api/document-categories/{category_id}`
- `PATCH /api/document-categories/{category_id}`
- `DELETE /api/document-categories/{category_id}`

Default document category seeds are defined in `src/db/seed/document_categories.py` and include
common broker and general business documents:

- `Identity Document`
- `Proof of Address`
- `Bank Statement`
- `Payslip`
- `Tax Notice`
- `Employment Contract`
- `Purchase Agreement`
- `Loan Application`
- `Loan Offer`
- `Insurance Certificate`
- `Property Valuation Report`
- `Company Registration Extract`
- `Invoice`
- `Receipt`
- `Purchase Order`
- `Signed Contract`

Custom application migrations are global and live under `src/db/`. They currently include the
`extraction_templates` and `document_categories` tables. Reference data is seeded separately from
migrations via `src/db/seed/` and is ensured automatically during app startup after migrations.
The migration state can be inspected with:

```bash
cd apps/api
set -a
. ./.env
set +a
uv run alembic -c src/db/alembic.ini current
```
