# API

The backend is an [Aegra](https://github.com/ibbybuilds/aegra) project that hosts a LangGraph
agent.

## Common Commands

Run these from the repo root:

```bash
pnpm api:deps
pnpm dev:api
pnpm build:api
pnpm lint:api
pnpm typecheck:api
pnpm docker:up
pnpm docker:down
```

Or run the package scripts directly from `apps/api/`:

```bash
pnpm dev
pnpm build
pnpm lint
pnpm typecheck
```

## Files

- `aegra.json`: graph registration for Aegra
- `pyproject.toml`: Python dependencies and tooling
- `src/little_john_test/graph.py`: main LangGraph definition
- `docker-compose.yml`: local PostgreSQL + API stack
