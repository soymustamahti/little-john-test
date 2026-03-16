---
name: interview-delivery
description: Use when planning, prioritizing, scoping, documenting, or reviewing work against the interview requirements, time limit, quality bar, and expected deliverables.
---

# Interview Delivery

Use this skill whenever you need to decide what to build, in what order, or how much detail is
worth adding.

## Priority Order

1. Structured extraction
2. Classification and routing
3. Correction chat agent
4. Validation pipeline
5. Real-time progress

## Delivery Heuristics

- Clean domain design beats broad but shallow features
- Good tests beat speculative infrastructure
- A minimal but coherent UI beats an overbuilt interface
- README design notes matter because evaluators will read them

## Review Checklist

Before calling something complete, verify:

- Types are explicit
- Edge cases are tested
- LLM boundaries are mockable
- Failure modes are handled clearly
- The implementation matches the interview prompt, not just local preferences

## Scope Guardrails

- Do not add a database
- Do not over-index on deployment or infra polish
- Keep the architecture extensible without making the codebase heavy
- Prefer parts that demonstrate judgment, reliability, and testability

## Documentation Expectations

Make sure later implementation updates:

- `README.md`
- any relevant design notes
- `.agent/memory.md`

## When In Doubt

Read:

- `.codex/references/interview-brief.md`
- `.codex/references/delivery-plan.md`
