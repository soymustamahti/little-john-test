# Agent Operating Manual

This repository is an interview prototype for a document intelligence platform that extracts,
validates, corrects, and exports structured data from uploaded documents.

## Current Phase

The repository is in a context-and-planning phase.

- Do not start product implementation unless the user explicitly asks.
- You may create or update context files, architecture notes, task breakdowns, and skill guides.
- If implementation starts later, preserve the architecture and quality constraints defined here.

## Mandatory Read Order

Before making meaningful changes, read these files in order:

1. `.agent/memory.md`
2. `.codex/references/repo-overrides.md`
3. `.codex/references/interview-brief.md`
4. `.codex/references/architecture-target.md`
5. `.codex/references/langgraph-system-blueprint.md`
6. `.codex/references/local-reference-repos.md`
7. `.codex/references/delivery-plan.md`
8. `.codex/references/acceptance-checklist.md`

Then read the relevant repo-local skill files:

- Frontend work: `.codex/skills/frontend-platform/SKILL.md`
- Backend and agent work: `.codex/skills/document-ai-backend/SKILL.md`
- Prompt and system-instruction work: `.codex/skills/agent-prompt-design/SKILL.md`
- Scope, prioritization, and delivery tradeoffs: `.codex/skills/interview-delivery/SKILL.md`

## Repository Truth

- Monorepo layout lives under `apps/`
- `apps/web`: Next.js frontend
- `apps/api`: Python 3.12 backend using Aegra today, with FastAPI-compatible architecture expected
- `apps/aegra`: local source repo for the framework and docs
- `apps/system-prompts-and-models-of-ai-tools`: local prompt corpus for prompt design reference
- The interview prompt is a baseline; user-approved production-ready deviations are allowed
- PostgreSQL is the default persistence choice when durable state materially improves the design
- The expected product is production-minded, but still optimized for an 8-hour interview exercise

## Non-Negotiable Product Goals

- Strong typed schemas for templates, extraction results, metadata, and validation issues
- Deterministic validation pipeline
- Robust handling of malformed LLM output
- Event-driven progress model for long-running extraction
- Undoable correction workflow
- Test coverage focused on failure modes and edge cases

## Required Working Style

- Favor separation of concerns and explicit boundaries over quick inline logic
- Keep LLM calls behind narrow interfaces so they are easy to mock in tests
- Keep routing, parsing, validation, and correction logic separate
- Never let UI components own request details directly if hooks can own them instead
- When deviating from the interview prompt, document the reason in the README and keep it
  evaluator-friendly
- When building later, update `.agent/memory.md` after each meaningful milestone

## Git Workflow

- The user will create the branch
- Work on the branch the user provides
- Commit only when the current work is coherent, runnable, and reviewable
- Push only completed milestones, not half-finished work
- Prefer a visible sequence of clean commits over one giant final commit

## Interview Priorities

If time becomes constrained later, prioritize in this order:

1. Part 1: structured extraction
2. Part 2: classification and routing
3. Part 3: correction chat agent
4. Part 4: validation pipeline
5. Part 5: real-time progress

## Context Files

- `.agent/memory.md`: current project memory and active decisions
- `.codex/references/repo-overrides.md`: user-approved deviations from the interview prompt
- `.codex/references/interview-brief.md`: normalized problem statement
- `.codex/references/architecture-target.md`: target system design and module boundaries
- `.codex/references/langgraph-system-blueprint.md`: LangGraph, ingestion, retrieval, and correction blueprint
- `.codex/references/local-reference-repos.md`: how to use the cloned Aegra repo and prompt corpus
- `.codex/references/delivery-plan.md`: phased delivery and quality bar
- `.codex/references/acceptance-checklist.md`: evaluator-ready definition of done
- `.codex/skills/*/SKILL.md`: repo-local implementation guides
