---
name: document-ai-backend
description: Use for backend, agent, extraction, classification, routing, validation, undo, event-driven orchestration, FastAPI, Aegra, and Python architecture work in apps/api.
---

# Document AI Backend

Use this skill for backend and agent work in `apps/api`.

## Core Principles

- Keep domain models explicit and typed
- Use LangGraph as the orchestration backbone
- Keep LLM adapters isolated from domain logic
- Keep deterministic validation outside the LLM
- Prefer event-driven orchestration over opaque linear pipelines
- Preserve undoability for every correction mutation

## Mandatory Boundaries

- Template modeling is separate from extraction logic
- Classification and routing are separate from extraction
- Parsing recovery is separate from prompt generation
- Validation is separate from extraction and correction
- Event streaming is separate from business logic

## Extraction Rules

- Never trust model output blindly
- Always validate and normalize parsed output
- Unknown keys, malformed nested objects, and invalid enum values must be handled deliberately
- Table rows require evidence; do not hallucinate them

## Routing Rules

- Route by file type and content quality
- Prefer simple deterministic preprocessing rules before model calls
- Support fallback strategies when text extraction is weak
- Cache classification results to avoid repeated work on the same document

## Ingestion Rules

- Treat ingestion as a first-class graph, not just a helper step
- OCR should happen before chunking when OCR is required
- Persist OCR output so it does not need to be recomputed
- Store originals in object storage and store metadata separately
- Chunking should be document-type aware, not uniform across all file types

## Retrieval Rules

- Use hybrid retrieval: keyword plus semantic
- Persist chunks and embeddings durably
- Rerank merged candidates before final evidence selection
- Keep provenance through every retrieval stage
- Spreadsheets should use structured parsing, not only text chunking

## Correction Agent Rules

- Mutations must go through explicit tools or service methods
- Every mutation must append to a reversible history
- Re-validation should happen after each mutation
- The agent should read targeted passages for large document sets instead of loading everything

## Progress Rules

- Treat long-running work as a stream of events
- Keep event payloads structured and replayable
- Include keepalive signals during long model calls

## Storage Rules

- The interview prompt allows no database, but this repo prefers production-ready persistence
- PostgreSQL is the default persistence choice when durable state is helpful
- In-memory adapters are acceptable for tests or narrow prototype seams
- Keep storage behind repository interfaces so services remain testable

Recommended durable data:

- users and auth data
- templates
- documents and derived artifacts
- extraction jobs
- correction history
- replayable progress events

## Testing Rules

- Mock LLM calls in tests
- Add direct tests for malformed or adversarial outputs
- Test undo behavior explicitly
- Test routing edge cases and validation edge cases

## When In Doubt

Read:

- `.codex/references/repo-overrides.md`
- `.codex/references/interview-brief.md`
- `.codex/references/architecture-target.md`
- `.codex/references/langgraph-system-blueprint.md`
- `.codex/references/delivery-plan.md`
