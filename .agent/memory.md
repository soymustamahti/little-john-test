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
- OCR direction is Mistral OCR
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
4. Build classification results and routing on top of the new `extraction_templates` and
   `document_categories` slices

## Latest Milestone

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
- Started the frontend implementation in `apps/web` with Axios, TanStack Query, and a
  template CRUD workspace UI
