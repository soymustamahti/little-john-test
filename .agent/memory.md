# Project Memory

## Status

- Phase: implementation started
- Current backend work includes the first real feature slices: `extraction_templates` and
  `document_categories`
- Repo structure is already a PNPM monorepo with `apps/api` and `apps/web`
- Root quality commands currently work for the existing scaffold

## Why This Repo Exists

This repository is for an interview exercise: build a prototype platform that extracts structured
data from documents, classifies documents, supports correction through chat, validates results,
and streams progress back to the client.

## Fixed Product Constraints

- Time budget is about 8 hours
- Python 3.12+ is required
- Deliverable is a GitHub repo with working code and README
- Strong tests are required, especially for malformed LLM output and validation edge cases

## User Preferences Locked In

- Frontend should use Next.js with Tailwind
- Use shadcn/ui for UI components when UI implementation starts
- UI should be minimalist, clear, and high-quality
- Use Axios for HTTP calls
- Use TanStack Query for request lifecycle and caching on the frontend
- Prefer hook-driven API access and clear separation of concerns
- Backend should remain Python-based and compatible with the current Aegra setup
- Backend orchestration should use LangGraph
- OCR direction is OpenAI OCR
- Original files should be stored in R2
- Retrieval should use both keyword and semantic search
- Retrieval results should be reranked before final evidence is used
- A deeper planning-capable LangGraph agent is expected for retrieval and correction
- `apps/aegra` is available locally as framework source and documentation
- `apps/system-prompts-and-models-of-ai-tools` is available locally as a prompt corpus
- Prompt design should be based on repeated patterns across that corpus, not on copying one prompt
- Authentication and a production-minded backend shape are expected later
- The interview prompt is a lower bound, not a hard upper bound
- If a database materially improves the platform, use one
- Default persistence choice should be PostgreSQL
- Future deviations from the prompt should be documented explicitly in the README
- The user will create working branches
- Commit and push should happen throughout implementation, but only for clean, committable
  milestones
- Do not push work-in-progress states just to save progress

## Architecture Direction

- Use an event-driven backend design
- Prefer durable persistence for core entities and job history instead of only in-memory state
- Persist chunks, embeddings, OCR outputs, and document metadata
- Prefer PostgreSQL plus pgvector for chunk and embedding storage
- Prefer PostgreSQL full-text search for keyword retrieval
- Keep LLM adapters isolated from domain logic
- Use the local Aegra repo as the first stop when framework behavior is unclear
- Add deterministic validation outside the LLM
- Support small-document direct context and large-document retrieval-on-demand
- Keep every correction mutation undoable
- Progress streaming should rely on an append-only event log with replay support

## Interview-Specific Guidance

- If implementation begins, prioritize Parts 1, 2, and 3 first
- Part 4 must remain deterministic and test-heavy
- Part 5 should be designed early even if implemented late because it affects orchestration
- The interview prompt says a minimal UI is enough, but this repo intentionally targets a more
  production-like split: Next.js frontend plus Python backend
- The prompt says no database is required, but the user explicitly prefers a database-backed design
  when it improves the result
- The user wants a LangGraph-heavy backend with ingestion, retrieval, and correction workflows
- The user expects OCR, chunking, embeddings, durable retrieval storage, and deep-agent retrieval
  planning
- The user wants a visible sequence of meaningful commits across the branch history

## Immediate Next Step

1. Keep the global FastAPI app separate from graph modules inside `apps/api`
2. Use Aegra source as the reference when import/loading behavior is unclear
3. Avoid root-level Alembic overrides in `apps/api` unless custom migrations are deliberately
   taking over that responsibility
4. Build classification results and routing on top of the new document ingestion slice plus the
   existing `extraction_templates` and `document_categories` modules

## Latest Milestone

- Migrated the frontend document-classification streaming client from a hand-rolled `fetch`/SSE
  parser to the official `@langchain/langgraph-sdk` browser client, including a shared
  `apps/web/lib/langgraph/client.ts` singleton and SDK-backed thread creation/run streaming in the
  web API layer
- Refined the document classification graph topology so the HITL acceptance path is represented as
  an explicit graph branch after `review_suggested_category`, which preserves behavior while making
  the LangSmith Studio visualization easier to explain during the interview
- Added a backend-focused walkthrough under `docs/backend-upload-and-process-document-walkthrough.md`
  that explains the upload flow, the process-document flow, the LangGraph/Aegra classification
  workflow, and the main design decisions behind the current implementation
- Added document classification persistence directly on `documents` with a linked
  `document_category_id`, lifecycle status, method, and lightweight JSON metadata for AI thread
  state, rationale, and suggested categories
- Added `DocumentClassificationService` plus document routes for manual classification and AI
  session bootstrap
- Replaced the placeholder Aegra graph registration with a real
  `document_classification_agent` graph that samples stored chunks, classifies against the seeded
  category catalog, streams progress with custom events, and interrupts for human review when a
  new category should be created
- Added the first frontend document-processing flow on the document detail page: upload now
  redirects to the document detail route, operators can launch `Process Document`, manually assign
  a category, or use the AI flow and review/accept/edit a suggested category inline
- Added focused backend tests for the new classification service and document classification routes
- Renamed the original template persistence model to `extraction_templates` to reflect that it
  defines extraction requirements, not document types
- Added `src/document_categories/` as a separate self-contained feature slice for predefined
  classification targets
- Added CRUD endpoints for extraction templates and document categories in the global FastAPI app
- Added a migration that renames the old `templates` table to `extraction_templates` and creates
  `document_categories`
- Added `src/db/seed/` with idempotent startup seeds instead of putting reference data in
  migrations
- Added seeded default document categories for common broker and general business uploads
- Added seeded starter extraction templates for vendor invoices, purchase orders, service
  contracts, and a French supplier invoice
- Added backend service tests for the new CRUD slices
- Added a shared custom Alembic environment in `src/db/` using the existing
  `little_john_test_alembic_version` table
- Kept Aegra's own root migration chain untouched
- Added an idempotent template seed command under `apps/api`
- Added `src/documents/` as a dedicated backend ingestion slice for upload, list, get, and delete
  operations
- Added a Cloudflare R2 storage adapter under `src/storage/` so original files are stored in object
  storage while PostgreSQL keeps the document metadata
- Added strict upload validation for PDF, common document images, DOCX, and spreadsheet formats
  (`.xlsx`, `.xls`, `.ods`, `.csv`), with Google Sheets expected to arrive as exported spreadsheet
  files
- Added a documents migration plus backend service tests covering validation failures and storage
  cleanup on persistence failure
- Added a frontend documents workspace under `apps/web` with upload, list, detail, and delete
  flows wired through Axios, React Query, and localized copy
- Replaced the placeholder documents nav item with a real workspace route and surfaced document
  counts alongside templates and categories in the shared setup stats
- Tightened backend upload concurrency behavior by moving validation off the event loop and
  reusing a single long-lived R2 client instead of constructing a new boto3 client per request
- Added a backend document content endpoint so the frontend can fetch stored originals for preview
  without depending on the bucket being publicly readable
- Added Gmail-style document preview modals in the frontend: inline iframe preview for PDFs,
  inline image preview for images, raw-text preview for DOCX, and workbook-style preview for
  spreadsheet formats
- Started the frontend implementation in `apps/web` with Axios, TanStack Query, and a
  template CRUD workspace UI
- Refined the frontend workspace so extraction templates and document categories are presented as
  separate configuration layers instead of a single generic "templates" screen
- Added frontend CRUD data flow and UI for document categories alongside the existing extraction
  template editor
- Split the frontend workspace into route-based list and detail pages for `extraction-templates`
  and `document-categories`, with a working sidebar and dedicated edit screens instead of the old
  split-pane layout
- Added frontend i18n scaffolding for static copy in `apps/web` with English and French JSON
  dictionaries, a shared locale provider, and a persisted language switcher wired through the
  Next.js layout via cookie-backed initial rendering plus local storage mirroring
- Added `label_key` to document categories across the backend model/API/seed path so seeded
  categories now expose a stable frontend translation handle while keeping `name` available as the
  classifier-facing English label
- Generated and applied Alembic revision `8147a5a57d83` to add `document_categories.label_key`,
  updated the reference seeds to key off `label_key`, and wired the frontend document category UI
  to display translated labels by key with fallback to the stored name
- Added a simple document content-processing pipeline to `src/documents/` that runs during upload:
  local PDF text extraction with OpenAI OCR fallback for low-text PDFs, OpenAI OCR for images,
  local DOCX and spreadsheet parsing, Chonkie recursive chunking, and OpenAI embeddings
- Added a documents migration that stores extracted text, processing metadata, and per-document
  chunk embeddings in PostgreSQL
- Kept the implementation intentionally small: synchronous processing inside upload for now,
  without background orchestration or retrieval indexing yet
- Added focused backend tests covering OCR fallback routing, DOCX/spreadsheet extraction, chunking,
  embedding persistence wiring, and upload failure behavior when processing fails
