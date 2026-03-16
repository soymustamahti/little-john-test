# Repo Overrides

This file records user preferences that intentionally go beyond the interview prompt.

## Principle

Treat the interview brief as a baseline, not a ceiling.

If the prompt says a simpler solution is acceptable but a stronger production-ready choice would
materially improve the system, prefer the stronger choice and document the rationale in the README.

## Active Overrides

### Production-Ready Bias

- Prefer production-ready architecture over the lightest possible prototype
- Favor durable state, explicit contracts, and maintainable boundaries
- It is acceptable to implement infrastructure the prompt says is optional when it materially
  improves correctness, traceability, security, or user experience

### Database

- The prompt says no database is required
- The user explicitly wants a database-backed design if it makes the platform stronger
- Default persistence choice should be PostgreSQL unless a later decision changes that

Suggested database-backed responsibilities:

- users and authentication data
- templates
- uploaded document metadata
- extraction jobs
- correction history and undo log
- progress events or replayable job events

### Authentication

- Authentication is allowed and desirable
- Prefer a clean user model and auth boundary instead of skipping auth for simplicity

### Design Rule For Deviations

When deviating from the interview prompt:

1. Keep the implementation coherent and proportional
2. Explain the deviation clearly in the README
3. Preserve strong tests and a runnable local setup
4. Avoid adding infra only for appearances

## Still Keep These Constraints

- Python 3.12+
- Strong tests
- Clear README
- Focus on evaluator-facing quality
- Avoid complexity that does not improve the product materially
