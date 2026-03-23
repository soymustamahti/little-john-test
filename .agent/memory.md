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
4. Build deterministic validation and correction flows on top of the new classification and
   extraction slices

## Latest Milestone

- Reworked the API reranking path so deployment builds no longer pull a local
  `sentence-transformers` and `torch` stack: hybrid retrieval reranking now uses a remote OpenAI
  Responses API call with structured output, controlled by `OPENAI_RERANKING_MODEL`, and falls
  back to fused keyword-plus-embedding ranking when OpenAI credentials are absent
- Reworked the document detail page into the post-processing home for a document: it now shows an
  inline source preview, a compact extraction overview, and the correction chat directly on the
  detail screen, while the confirm-review action closes the processing panel and returns the
  operator to that detail view instead of leaving them inside the workflow card
- Locked the detail-page process action once an extraction is confirmed, while still allowing a
  dedicated "continue review" path for pending-review extractions so already processed documents
  are not reprocessed accidentally
- Hardened the correction-chat finalizer boundary so correction runs no longer fail when the
  model emits an empty patch like `updates: []`; the correction schema now normalizes empty or
  module-list-shaped patches before validation, trims finalizer text fields defensively, and keeps
  the typed merge path intact
- Reworked the extraction correction UI into a more explicit ChatGPT-style workspace with message
  bubbles, quick correction prompts, a dedicated live-activity rail, keyboard send shortcuts, and
  clearer streaming visibility while preserving the existing correction-session backend flow and
  persisted chat history
- Added the first chat-based extraction-correction slice across backend and frontend: operators can
  now open a correction chat on an extraction draft, ask a deep LangGraph correction agent to fix
  values or re-search document evidence, watch live streamed correction activity, and persist the
  revised draft plus chat history back into `document_extractions`
- Added a comprehensive end-to-end walkthrough under
  `docs/end-to-end-document-workflow-walkthrough.md` that explains the live repository workflow
  from upload and digestion through classification, extraction, streaming, review, persistence,
  typed contracts, and code-reading order, while clearly separating current implementation from
  still-planned interview targets
- Fixed the extraction review visibility bug by tightening the extraction finalizer contract:
  the LangGraph finalizer now produces a typed compact result payload instead of an unconstrained
  generic dict, avoids prompting the model with an all-null output skeleton, and runs a repair
  pass when the first structured result comes back empty even though the reasoning summary found
  evidence
- Verified the fix live against the `convention mandat MSH.pdf` document: the extraction row in
  PostgreSQL now stores populated field values and the `/api/documents/{id}/extraction` API
  returns them for the frontend review UI instead of an all-null template-shaped skeleton
- Updated the extraction review UI so confidence percentages remain visible but are no longer
  editable inputs; only extracted values remain operator-editable during review
- Added the first structured-extraction slice across backend and frontend: documents can now start
  a dedicated AI extraction session for a chosen extraction template, stream progress from a new
  `document_extraction_agent`, persist a reviewable extraction draft, and confirm edited
  extraction values plus confidence scores from the UI
- Implemented a minimal but explicit LangGraph extraction agent under
  `src/agents/document_extraction_agent/` that uses hybrid retrieval tools
  (`keyword_search`, `semantic_search`, `hybrid_search`, `inspect_chunk`, and pandas-backed
  `inspect_spreadsheet`) before handing off to a structured finalizer step
- Added `document_extractions` persistence plus backend service and router coverage for extraction
  session bootstrap, draft retrieval, and human-reviewed extraction confirmation
- Extended the document-processing panel so operators now pick an extraction template up front,
  let AI/manual classification continue as before, and then review/edit extracted fields in
  template-shaped inputs while confidence remains visible as read-only review information
- Reworked the document-classification prompt using patterns sampled from the local
  `apps/system-prompts-and-models-of-ai-tools` corpus plus mini-agent analysis: the prompt now
  uses explicit Mission/Evidence Boundary/Decision Policy/Language Policy/Output Contract sections
  and requires the rationale and suggested category name to follow the document's dominant language
- Hardened document-category label-key normalization for multilingual suggestions by transliterating
  accented characters before snake_case normalization in both backend and frontend helpers, and
  added focused backend tests covering accented French category suggestions
- Improved the frontend AI document-classification operator flow so the processing panel no longer
  resets out of AI mode when document refetches change the classification status, and added a live
  event timeline with raw payload inspection by streaming LangGraph `custom`, `updates`, and
  `values` events into the UI
- Refined the AI classification event view into a compact operator activity feed that shows only
  meaningful steps without internal scrolling, and reduced the visible stream noise by surfacing
  `custom` progress events plus interrupt/completion/error states instead of every state update
- Fixed duplicate human-review entries in the frontend activity feed by no longer explicitly
  requesting LangGraph `values` mode for the classification run and deduplicating adjacent
  interrupt events, since Aegra already remaps interrupt-only updates to `values` events for
  compatibility
- Normalized AI-suggested category names away from snake_case-style display by adding backend
  category-name normalization, stronger classifier prompt guidance, frontend humanized fallback
  rendering, and focused service tests for suggestion/acceptance flows
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
- Added the first LangGraph-based extraction workflow with reviewable draft persistence, hybrid
  retrieval tools, and editable confidence-backed extraction review in the frontend processing
  panel
- Hotfixed the extraction finalizer to use OpenAI function-calling structured output instead of
  the stricter `response_format` path, which rejected the discriminated extraction schema
- Updated extraction progress streaming so retrieval/tool activity emits specific messages and the
  frontend updates the active progress row in place instead of stacking duplicate
  "planning_and_retrieving" timeline blocks
- Relaxed the extraction finalizer response schema to accept a draft payload, then normalize the
  result deterministically against the chosen template before strict validation so missing `kind`
  discriminators or list-shaped evidence no longer crash the run
- Added a hard extraction evidence-collection budget in the LangGraph loop to prevent runaway
  model/tool turns from causing excessive OpenAI retries and rate-limit pressure during finalization
- Added a dedicated seeded French extraction template for "Convention de mandat de maîtrise
  d'ouvrage", based on the `convention mandat MSH.pdf` test document, with modules for
  identification, parties, financial terms, and annexes
- Relaxed the finalizer draft summary schema and added deterministic summary trimming so verbose
  `reasoning_summary` text from the LLM can no longer crash extraction runs during structured
  output parsing
- Reworked the extraction correction chat into a single conversation layout with inline,
  collapsible per-turn activity explorers, compact event summaries, and full-width assistant
  replies so streaming agent activity feels closer to ChatGPT/Codex instead of a split chat plus
  side activity rail
- Confirmed the document retrieval stack is hybrid by design and now enabled the intended
  cross-encoder reranking path by adding `sentence-transformers`, while also making the shared
  extraction/correction tool list hybrid-first with separate keyword and semantic tools still
  exposed for targeted use
- Cleaned up the document-detail/process-review frontend flow: interactive controls now advertise
  clickability better, pending category suggestions collapse immediately after a decision, the
  detail page only shows extraction results and correction chat after confirmation, confidence
  indicators are compact chips instead of input-looking boxes, and extraction-template editing now
  uses collapsible module/field sections for a denser readable layout
- Persisted the correction-chat event explorers across the confirm/revisit flow on the frontend:
  the detail-page correction chat now restores each turn's collapsible agent-activity groups after
  the component remounts, so the operator can still inspect what the deep correction agent did even
  after confirming extraction and returning to the document detail view
- Adjusted the document-detail extraction workspace visibility so a previously confirmed document
  keeps showing its saved extraction overview and correction chat when later corrections push the
  extraction back to `pending_review`; duplicate UI is still avoided while the dedicated processing
  drawer is open
- Promoted correction-chat activity explorers from transient UI state into persisted extraction
  metadata: correction event groups are now saved via a dedicated API path, returned by
  `/api/documents/{id}/extraction`, reused by both review and confirmed-detail chats, and preserved
  when the operator confirms extraction or revisits the document later
- Updated the correction-chat activity persistence cadence so event groups are pushed while the
  stream is still running instead of waiting for the final refresh, which keeps the event explorer
  aligned with real-time correction activity
- Removed `document_id` from the model-visible retrieval tool schemas in both extraction and
  correction graphs by switching the shared tool list to `StructuredTool` wrappers with
  `InjectedState("document_id")`; the graph now injects the document context itself, preventing
  malformed LLM-generated UUIDs from crashing retrieval tool calls like `inspect_chunk`
- Fixed a frontend race in the correction chat streaming flow: opening a correction session no
  longer invalidates the extraction query before the live stream starts, the chat marks itself as
  streaming before session bootstrap, and server-sync effects now preserve the optimistic user turn
  until the backend refresh catches up, so live correction events stay visible in real time
- Hardened correction-chat event syncing against stale backend snapshots: the UI now prefers the
  more advanced local event-group state when the server is behind on status, item count, or
  expanded/collapsed state, and correction-activity mutation responses no longer regress the query
  cache when an older save finishes after a newer one
  <<<<<<< HEAD
  =======
- Extended the frontend onboarding tour into a document-processing walkthrough that preloads the
  `convention mandat MSH.pdf` sample, uploads it, drives AI classification/extraction, sends a
  correction prompt, and now conditionally accepts a suggested category when classification pauses
  for human review instead of assuming the document always auto-matches an existing category
- Switched frontend PDF/image previews from direct backend content URLs to browser `blob:` URLs
  created from fetched bytes so the inline preview no longer depends on the browser PDF viewer
  streaming the API endpoint directly, which was causing previews to appear while staying stuck in
  a perpetual loading state
- Hardened the onboarding upload-to-detail transition so the Joyride does not advance on route
  change alone: the document-detail step now waits for the actual process button to mount on the
  `/documents/:id` screen before presenting the next tooltip, preventing the step-8 handoff from
  skipping or breaking on slower detail-page loads
- Expanded the correction segment of the onboarding tour so it highlights both the SIRET field and
  the “Adresse du mandataire” field before sending the correction, locks the live correction
  activity step until the agent finishes updating both values, then shows the corrected SIRET and
  corrected address separately before the final review confirmation
- Tightened the onboarding tour interaction model so normal Joyride steps expose only the primary
  button and globally block clicks on the underlying page, preventing accidental clicks on upload
  or other workspace actions from desynchronizing the walkthrough
  > > > > > > > origin
