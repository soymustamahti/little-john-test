# Project Memory

## Status

- Phase: context and planning only
- Product implementation has not started yet
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
- Authentication and a production-minded backend shape are expected later
- The interview prompt is a lower bound, not a hard upper bound
- If a database materially improves the platform, use one
- Default persistence choice should be PostgreSQL
- Future deviations from the prompt should be documented explicitly in the README

## Architecture Direction

- Use an event-driven backend design
- Prefer durable persistence for core entities and job history instead of only in-memory state
- Persist chunks, embeddings, OCR outputs, and document metadata
- Prefer PostgreSQL plus pgvector for chunk and embedding storage
- Prefer PostgreSQL full-text search for keyword retrieval
- Keep LLM adapters isolated from domain logic
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

## Immediate Next Step

Wait for the user to explicitly approve implementation work.

When implementation starts:

1. Finalize package and module layout in `apps/api`
2. Install frontend UI and state libraries in `apps/web`
3. Design the LangGraph ingestion, retrieval, and correction graph boundaries
4. Define PostgreSQL, pgvector, and R2 persistence models
5. Implement the template and extraction domain models first
6. Add tests alongside each backend subsystem from the beginning
