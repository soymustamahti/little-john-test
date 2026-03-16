# Delivery Plan

## Goal

Maximize evaluator confidence within a limited time budget by producing a clean, testable
prototype instead of a broad but fragile demo.

## Recommended Build Order

### Phase 0: Foundations

- Confirm stack and file layout
- Lock core domain vocabulary
- Prepare README and agent context
- Define testing strategy before implementation

### Phase 1: Core Domain

- Template schema
- Extraction result schema
- Field metadata schema
- Validation issue schema
- Document descriptor schema

### Phase 2: Extraction Resilience

- Prompt builder
- LLM output parser
- Recovery pipeline for malformed outputs
- Non-hallucinating table logic
- Tests for adversarial responses

### Phase 3: Classification and Routing

- Classification result model
- Routing strategy abstraction
- Preprocessing strategy selection
- Classification cache
- Tests for edge cases and fallback behavior

### Phase 4: Correction Agent

- Correction state model
- Mutation log and undo
- Tool contract
- Document search or retrieval path
- Chat API and minimal UI

### Phase 5: Validation and Progress

- Deterministic validation engine
- SSE or equivalent progress stream
- Reconnect and replay behavior

## Time Pressure Rules

If the project becomes time-constrained:

1. Keep the domain model clean
2. Keep tests strong around parser recovery and validation
3. Deliver a minimal but credible correction flow
4. Add infrastructure only when it materially improves the product and can be justified clearly

## Definition Of Done

A part is only done when:

- types are explicit
- tests exist for happy path and failure path
- the API or UI surface is coherent
- README and design notes reflect the implementation

## Commit And Push Cadence

When implementation starts:

- work on the branch the user created
- commit only coherent, reviewable slices
- push after the slice is stable enough to stand on its own
- do not push half-finished or knowingly broken work

Good commit points:

- a backend subsystem with tests passing
- a frontend feature with its data flow and UI states wired correctly
- a schema or migration set that matches the code using it

## What Not To Do

- Do not add a database unless the user explicitly changes the constraint
- Do not hide critical logic inside prompts without deterministic safeguards
- Do not let frontend components make ad hoc raw fetches when hooks can own the data flow
- Do not optimize for cleverness over readability

## Approved Deviations

The user has explicitly approved production-ready deviations from the interview prompt.

Examples:

- using PostgreSQL instead of only in-memory state
- introducing authentication
- adding stronger persistence for jobs, events, and correction history

These deviations are allowed when:

- they materially improve the platform
- they do not destabilize delivery
- they are explained in the README as intentional choices
