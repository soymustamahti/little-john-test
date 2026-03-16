# little-john-test

A PNPM-managed monorepo with:

- `apps/web/`: a Next.js web application
- `apps/api/`: an Aegra/LangGraph Python backend

## Prerequisites

- Node.js 22+
- PNPM 10+
- Python 3.12+
- `uv`

## Setup

```bash
cp apps/api/.env.example apps/api/.env
pnpm setup
```

`pnpm setup` installs the JavaScript workspace dependencies from the repo root, then syncs the
Python environment in `apps/api/`.

## Workspace Scripts

Run these from the repository root:

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

## Structure

```text
.
|-- apps/
|   |-- api/
|   |   |-- package.json
|   |   |-- pyproject.toml
|   |   |-- aegra.json
|   |   +-- src/
|   +-- web/
|       |-- package.json
|       +-- app/
|-- package.json
+-- pnpm-workspace.yaml
```
