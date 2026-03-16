---
name: frontend-platform
description: Use for any work in apps/web involving Next.js, Tailwind, shadcn/ui, Axios, TanStack Query, hooks, component structure, or review and correction UI architecture.
---

# Frontend Platform

Use this skill for all work inside `apps/web`.

## Defaults

- Next.js App Router
- TypeScript strict mode
- Tailwind CSS for styling
- shadcn/ui for reusable UI primitives
- Axios for HTTP transport
- TanStack Query for request state, caching, and mutations

## UI Direction

- Keep the UI minimalist and calm
- Favor clarity over visual noise
- Every screen must make the next action obvious
- Always show loading, empty, error, and success states
- Make validation issues and confidence signals easy to scan

## Component Rules

- Keep presentational components separate from data hooks
- Feature components may compose smaller presentational subcomponents
- Avoid giant page files that own all state and rendering logic
- Keep view-specific formatting near the component, but keep request logic in hooks or API layers

## Data Access Rules

- Do not call Axios directly from page components
- Put Axios configuration in `lib/api`
- Wrap server interactions in React Query hooks under `hooks`
- Expose stable hook APIs that future UI can reuse

## Suggested Layout

- `components/ui`: shadcn/ui primitives
- `components/features`: document upload, extraction state, validation panel, correction chat
- `hooks`: query hooks and UI state helpers
- `lib/api`: Axios client, endpoint clients, request helpers
- `providers`: query provider and any app providers
- `types`: frontend-only view models or shared API contracts

## UX Rules For This Project

- The correction screen should show chat, current extraction state, and validation issues together
- Confidence and validation severity should be visually distinct but not noisy
- Undo must be immediately available
- Progress streaming should feel live and trustworthy

## When In Doubt

Read:

- `.codex/references/architecture-target.md`
- `.codex/references/delivery-plan.md`
