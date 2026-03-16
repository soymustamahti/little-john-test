# Local Reference Repos

This repository contains two cloned local reference repos that future agents should use as source
material when relevant.

## `apps/aegra`

Purpose:

- local source of truth for the self-hosted backend framework in use
- framework-compatible patterns for LangGraph, FastAPI, PostgreSQL, auth, streaming, and storage

How to use it:

- if there is any doubt about Aegra behavior, read local source before guessing
- prefer `apps/aegra/CLAUDE.md` for the high-level development guide
- prefer `apps/aegra/docs/` for conceptual documentation
- prefer `apps/aegra/libs/` when verifying implementation details

Useful entry points:

- `apps/aegra/CLAUDE.md`
- `apps/aegra/README.md`
- `apps/aegra/docs/quickstart.mdx`
- `apps/aegra/docs/openapi.json`
- `apps/aegra/docs/llms.txt`

Use cases:

- understanding Aegra graph loading and configuration
- checking how Aegra handles auth, store, streaming, and custom routes
- validating assumptions before adding backend architecture on top of it

## `apps/system-prompts-and-models-of-ai-tools`

Purpose:

- local corpus of prompts and tool definitions used by many AI coding and agent products
- reference material for writing our own system prompts and agent instructions

How to use it:

- treat it as a comparative corpus, not as code to copy
- read multiple prompt families before designing our prompts
- extract repeated patterns and adapt them to this project
- never cargo-cult tool names or product-specific behaviors that do not fit our system

Useful folders to sample first:

- `apps/system-prompts-and-models-of-ai-tools/Amp/`
- `apps/system-prompts-and-models-of-ai-tools/Cursor Prompts/`
- `apps/system-prompts-and-models-of-ai-tools/Anthropic/`
- `apps/system-prompts-and-models-of-ai-tools/Manus Agent Tools & Prompt/`
- `apps/system-prompts-and-models-of-ai-tools/VSCode Agent/`

Prompt design patterns worth extracting:

- clear role and scope
- completion bias without unnecessary verbosity
- explicit tool-use boundaries
- planning and execution separation
- progress transparency
- guardrails for risky actions
- formatting discipline
- stop conditions and handoff behavior

## Rule For Both Repos

- They are references, not direct implementation requirements
- Use them to verify behavior, discover good patterns, and avoid unnecessary invention
- When a pattern from a reference repo is adopted, adapt it to our architecture and document why
