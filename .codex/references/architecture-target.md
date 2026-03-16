# Architecture Target

## System Shape

The target system should be event-driven and split into clear layers:

- Ingestion and file handling
- Document classification
- Routing and preprocessing
- Extraction
- Deterministic validation
- Correction agent and undo log
- Progress event streaming
- Frontend review and chat UI

## Backend Direction

Keep the backend centered on pure domain models plus orchestration adapters.

The preferred orchestration engine is LangGraph.

Recommended logical modules inside `apps/api`:

- `domain/`
  - templates
  - extraction results
  - validation issues
  - document descriptors
- `services/`
  - ingestion
  - classification
  - routing
  - extraction
  - retrieval
  - reranking
  - validation
  - correction
  - export
- `events/`
  - event models
  - event bus
  - event replay
- `llm/`
  - OCR adapters
  - prompt builders
  - provider adapters
  - output parsing
- `api/`
  - FastAPI routes
  - request and response schemas
  - streaming endpoints
- `storage/`
  - database repositories
  - event store
  - file and blob metadata store
  - optional local development adapters

## LangGraph Subsystems

The target backend should expose multiple graph-backed workflows instead of one generic agent.

Expected graph families:

- ingestion graph
- retrieval graph
- correction graph

See `.codex/references/langgraph-system-blueprint.md` for the detailed intended behavior.

## Event-Driven Model

Design around domain events rather than a single giant pipeline function.

Expected event families:

- `document.uploaded`
- `document.classified`
- `document.routed`
- `document.preprocessed`
- `extraction.started`
- `extraction.completed`
- `validation.completed`
- `correction.applied`
- `correction.undone`
- `progress.updated`
- `error.recorded`

The event system should enable:

- real-time progress streaming
- replay after client reconnection
- auditability of user corrections
- undo support through explicit mutation history
- long-running ingestion and retrieval workflows with durable progress state

## Extraction Model

Every extracted field should carry:

- normalized value
- raw value if needed
- confidence
- source location
- extraction mode: direct or inferred

Table extraction rules:

- Only emit rows supported by document evidence
- Keep row provenance when possible
- Prefer empty arrays over guessed rows

## LLM Boundary Rules

- Never trust raw model output
- Parse in layers: raw text -> recovery -> schema validation -> normalization
- Reject unknown field keys unless explicitly mapped
- Clamp or reject invalid enum values
- Recover from stringified JSON and truncated responses when reasonable
- Keep prompts separate from parsing and validation

## Correction Agent Design

The correction agent should act on explicit tools instead of hidden mutations.

Expected tool families:

- read current extraction state
- update scalar field
- add table row
- edit table cell
- remove table row
- search source documents
- re-check a page or document slice
- run validation
- undo last mutation

State changes should:

- append a mutation event
- generate a new state snapshot
- trigger validation
- return a user-readable summary

## Frontend Direction

Keep `apps/web` split into:

- `components/ui`: shadcn/ui primitives
- `components/features`: feature-specific UI
- `hooks`: React Query hooks and UI state helpers
- `lib/api`: Axios client and API adapters
- `types`: shared frontend types
- `providers`: query provider and app-level providers

The correction UI should show:

- document and extraction summary
- current validation issues
- chat thread
- current extraction state
- undo affordance
- progress feedback during extraction

## Streaming Strategy

Use server-sent events by default unless a later requirement forces WebSockets.

Reasoning:

- simpler for one-way progress streams
- good fit for keepalive events
- easier replay model when backed by an event log

The stream contract should support:

- `event_id`
- `job_id`
- `phase`
- `progress`
- `payload`
- `timestamp`

## Search and Retrieval Direction

Preferred retrieval stack:

- PostgreSQL full-text search for keyword retrieval
- pgvector for semantic retrieval
- reranking after candidate merge
- evidence assembly with page, sheet, or chunk provenance

The retrieval and correction agent should use both keyword and semantic search instead of relying
on only one method.

## Storage Direction

The interview prompt allows a database-free prototype, but the repo preference is now
production-biased.

Default persistence direction:

- PostgreSQL for durable application data
- repository layer so core services stay storage-agnostic
- explicit event persistence for progress replay and correction history
- local file storage for uploaded files in development, with a clean abstraction for later object
  storage if needed

Suggested durable entities:

- users
- templates
- uploaded documents and derived artifacts
- OCR outputs
- chunks
- embeddings
- extraction jobs
- job progress events
- correction mutations and undo history

In-memory adapters are still acceptable for tests and narrow prototype-only seams, but they should
not be the primary architecture target anymore.

## Testing Direction

Test the system from the inside out:

1. domain models and validators
2. LLM output parser recovery paths
3. routing decisions
4. correction state mutations and undo
5. API contracts
6. minimal UI interaction tests where worth it
