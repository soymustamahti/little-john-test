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
- `src/main.py`: global FastAPI app mounted by Aegra
- `src/agents/little_john_test/graph.py`: current LangGraph definition
- `docker-compose.yml`: local PostgreSQL + API stack

## Aegra Integration Notes

- `http.app` is loaded as the module `src.main:app` because Aegra supports module imports for
  custom FastAPI apps and this avoids fragile file-path import behavior.
- Graphs remain file-based in `aegra.json`, which matches how Aegra loads graph exports.
- Avoid adding a root `alembic.ini` in `apps/api` unless you intentionally want to override
  Aegra's own migration chain.
