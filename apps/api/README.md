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
pnpm seed:reference
```

## Docker

Build the API image from the repo root so the Docker build context matches deployment platforms
that build from the repository root:

```bash
docker build -f apps/api/Dockerfile -t little-john-api .
```

For managed PostgreSQL, prefer `DATABASE_URL`. The backend still supports individual
`POSTGRES_*` variables for local compose usage.

## Files

- `aegra.json`: graph registration for Aegra
- `pyproject.toml`: Python dependencies and tooling
- `src/main.py`: global FastAPI app mounted by Aegra
- `src/agents/document_classification_agent/graph.py`: document classification LangGraph workflow
- `src/extraction_templates/`: extraction template feature slice with CRUD
- `src/document_categories/`: document category feature slice with CRUD
- `src/documents/`: document ingestion plus classification feature slice
- `src/storage/`: object-storage abstractions and the Cloudflare R2 adapter
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
Each category now keeps:

- `name`: the classifier-facing label, which can remain in English for model prompts
- `label_key`: the stable frontend translation key used to render a localized label in the UI

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

Reference data can also be seeded manually with:

```bash
cd apps/api
pnpm seed:reference
```

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

## Documents

The document ingestion feature is implemented as a dedicated slice under `src/documents/`.
Uploaded files are stored in Cloudflare R2, while document metadata stays in PostgreSQL.

Available endpoints:

- `GET /api/documents`
- `POST /api/documents`
- `GET /api/documents/{document_id}`
- `POST /api/documents/{document_id}/classification/manual`
- `POST /api/documents/{document_id}/classification/ai-session`
- `DELETE /api/documents/{document_id}`

The document detail record now also stores:

- the final linked `document_category_id`
- classification lifecycle state and method
- lightweight classification metadata for AI thread state, rationale, and suggested categories

The Aegra graph registered in `aegra.json` is now `document_classification_agent`. It reads the
stored extracted text and persisted chunks, samples an excerpt based on
`DOCUMENTS_CLASSIFICATION_EXCERPT_CHARS`, compares it against the current document category
catalog, and then:

- directly links the document to an existing category when a good match exists
- or suggests a new category and pauses with a human-in-the-loop interrupt before creating it

The frontend streams this graph through Aegra's `/threads/.../runs/stream` endpoint using custom
progress events plus a review/resume step for pending category suggestions.

The upload endpoint accepts multipart form data with a single `file` field and validates:

- PDFs: `.pdf`
- Images: `.png`, `.jpg`, `.jpeg`, `.webp`, `.tif`, `.tiff`, `.bmp`
- Word documents: `.docx`
- Spreadsheets: `.xlsx`, `.xls`, `.ods`, `.csv`

Google Sheets uploads are supported through exported spreadsheet files such as `.xlsx`, `.ods`, or
`.csv`. Native Google Drive document identifiers are not part of this endpoint yet.

Environment settings used by this slice:

- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_PUBLIC_URL`
- `DOCUMENTS_MAX_UPLOAD_SIZE_BYTES`

`R2_PUBLIC_URL` is optional and should point to a true public bucket base URL, such as a custom
domain or an `r2.dev` URL. If it points at the S3 API endpoint instead, the API will keep
`public_url` empty for uploaded documents.
