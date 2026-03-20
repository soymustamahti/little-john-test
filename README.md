# little-john-test

Prototype repository for an interview exercise: build a document intelligence platform that can
classify uploaded files, extract structured data from them, validate the results, let the user
correct mistakes through chat, and stream progress in real time.

## Current Status

This repository is now in early implementation.

- The monorepo structure is ready
- `apps/api` already exposes template CRUD with PostgreSQL-backed persistence
- `apps/api` now also exposes document upload, list, get, and delete endpoints with PostgreSQL
  metadata persistence plus Cloudflare R2 object storage
- `apps/api` now also exposes the first document-classification slice: manual category assignment,
  AI classification session bootstrap, and an Aegra/LangGraph document-classification agent with
  streamed progress plus human review for suggested new categories
- `apps/api` now also exposes the first structured-extraction slice: AI extraction session
  bootstrap, a LangGraph extraction agent with hybrid retrieval tools, persisted reviewable
  extraction drafts, a correction-chat assistant for draft revisions, and confirmation endpoints
  for human-reviewed extraction results
- `apps/web` now includes a documents workspace for upload, list, detail, and delete flows in
  addition to the existing template and document-category screens
- `apps/web` now includes a document-processing flow on the document detail page for manual or AI
  classification, including review of AI-suggested categories plus template-driven extraction
  review with editable values, read-only confidence, and a correction chat that can revise the
  draft through a streamed deep-agent run
- `apps/web` now includes the first real operator UI for template management
- Agent guidance files remain part of the repository so future slices follow the same constraints

## Product Goal

The target product should support this workflow:

1. A user defines a template describing what to extract
2. The user uploads one or more documents
3. The system classifies and routes each document
4. The system extracts structured data plus quality metadata
5. The user reviews and corrects the extraction through chat
6. The user exports the final structured output

## Chosen Repository Direction

This repo intentionally uses a production-minded split even though the interview would allow a
lighter solution:

- `apps/api`: Python backend
- `apps/web`: Next.js frontend
- root workspace: PNPM monorepo orchestration

The backend is expected to stay compatible with the current Aegra-based setup while moving toward
an event-driven, FastAPI-friendly architecture for the actual feature work.

The current backend direction is now more concrete:

- LangGraph for ingestion, retrieval, and correction workflows
- OpenAI OCR for OCR-capable ingestion
- R2 for original document storage
- PostgreSQL plus pgvector for durable metadata, chunks, and embeddings
- hybrid retrieval with keyword search, semantic search, and reranking

Current prototype note:

- the new extraction slice intentionally keeps retrieval simple and explainable for the interview:
  the extraction agent uses stored chunk embeddings, keyword overlap scoring, hybrid candidate
  merging, chunk inspection, and pandas-backed spreadsheet preview tools before producing a
  reviewable extraction draft

## Important Repository Override

The original interview prompt says some infrastructure is optional, including a database.

This repository does not treat those statements as hard limits. The goal here is to build the best
production-ready version that remains coherent and explainable. If a database, authentication, or
other stronger architectural choice materially improves the result, it is allowed and preferred.

The important rule is not "stay minimal at all costs." The important rule is "make stronger choices
deliberately and justify them clearly in the README and design notes."

## Locked Technical Preferences

- Frontend: Next.js, Tailwind, shadcn/ui, Axios, TanStack Query
- Backend: Python 3.12+, typed models, event-driven orchestration, deterministic validation
- Agent architecture: LangGraph-based ingestion, retrieval, and correction workflows
- OCR: Mistral OCR
- Retrieval: hybrid keyword plus semantic search with reranking
- File storage: R2 for original uploaded files
- Persistence: PostgreSQL is the default target when durable state improves the system
- Auth: allowed and encouraged if it supports a cleaner production-ready platform
- Testing: strong coverage on malformed LLM outputs, validation logic, routing, and undo behavior

## AI Context Files

The repository now contains explicit context for future agent sessions:

- [AGENTS.md](./AGENTS.md): primary operating manual
- [.agent/memory.md](./.agent/memory.md): current project memory
- [.codex/references/interview-brief.md](./.codex/references/interview-brief.md): normalized test brief
- [.codex/references/repo-overrides.md](./.codex/references/repo-overrides.md): user-approved deviations from the prompt
- [.codex/references/architecture-target.md](./.codex/references/architecture-target.md): target architecture
- [.codex/references/langgraph-system-blueprint.md](./.codex/references/langgraph-system-blueprint.md): LangGraph ingestion and retrieval blueprint
- [.codex/references/local-reference-repos.md](./.codex/references/local-reference-repos.md): how to use the cloned framework and prompt repos
- [.codex/references/delivery-plan.md](./.codex/references/delivery-plan.md): build order and scope rules
- [.codex/references/acceptance-checklist.md](./.codex/references/acceptance-checklist.md): evaluator-ready checklist
- `.codex/skills/*/SKILL.md`: repo-local implementation guides

## Local Reference Repos

Two local repos are intentionally present as reference material:

- `apps/aegra`: framework source, docs, and implementation details
- `apps/system-prompts-and-models-of-ai-tools`: prompt corpus used to derive stronger prompt patterns

They are there so future implementation work can verify framework behavior directly and design
prompts from a broader corpus instead of improvising from memory.

## Workspace

This is a PNPM-managed monorepo.

### Layout

```text
.
|-- apps/
|   |-- api/
|   +-- web/
|-- AGENTS.md
|-- .agent/
|-- .codex/
|-- package.json
+-- pnpm-workspace.yaml
```

### Setup

```bash
cp apps/api/.env.example apps/api/.env
pnpm setup
```

### Root Commands

```bash
pnpm dev
pnpm dev:web
pnpm dev:api
pnpm build
pnpm lint
pnpm typecheck
pnpm check
pnpm docker:up
pnpm docker:down
```

## Interview Priorities

If execution time becomes tight later, the expected implementation order is:

1. Structured extraction
2. Classification and routing
3. Correction chat agent
4. Validation pipeline
5. Real-time progress

## Notes For Future Implementation

- Keep LLM calls behind narrow interfaces
- Never trust raw model output directly
- Make correction mutations undoable
- Treat progress as a replayable event stream
- Update README and `.agent/memory.md` as the product evolves
