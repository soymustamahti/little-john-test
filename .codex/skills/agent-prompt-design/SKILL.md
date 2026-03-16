---
name: agent-prompt-design
description: Use for any work on system prompts, agent instructions, tool prompts, correction prompts, extraction prompts, or prompt architecture. Consult the local prompt corpus in apps/system-prompts-and-models-of-ai-tools before designing prompts.
---

# Agent Prompt Design

Use this skill for any prompt or agent-instruction work.

## Mandatory Inputs

Before writing or revising prompts, read:

- `.codex/references/local-reference-repos.md`
- `.codex/references/repo-overrides.md`
- `.codex/references/langgraph-system-blueprint.md`

Then inspect relevant prompt samples from:

- `apps/system-prompts-and-models-of-ai-tools/`

## Prompt Design Method

Do not base our prompts on a single sample.

Instead:

1. sample several prompt families
2. identify recurring design patterns
3. keep only patterns that fit this project
4. write our prompts in our own language and structure

## Patterns To Look For

- role clarity
- tool discipline
- planning rules
- execution bias
- formatting rules
- state management cues
- error and fallback behavior
- stop conditions

## What To Avoid

- copying prompt text verbatim
- importing tool contracts that do not exist in our system
- inheriting vendor-specific assumptions
- overloading prompts with domain logic that belongs in code

## Project-Specific Prompt Needs

We will eventually need prompts for:

- document classification
- structured extraction
- correction agent behavior
- retrieval planning
- evidence inspection
- validation explanation

## Strong Default

Prefer prompts that are:

- explicit
- scoped
- tool-aware
- calm in tone
- deterministic where possible
- paired with code-side validation and recovery

## When In Doubt

Read:

- `.codex/references/local-reference-repos.md`
- `.codex/references/interview-brief.md`
- `.codex/references/langgraph-system-blueprint.md`
