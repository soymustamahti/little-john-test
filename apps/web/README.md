# Web

The frontend is a Next.js app wired into the root PNPM workspace.

## Common Commands

Run these from the repo root:

```bash
pnpm dev:web
pnpm build:web
pnpm lint:web
pnpm typecheck:web
```

Or run the package scripts directly from `apps/web/`:

```bash
pnpm dev
pnpm build
pnpm lint
pnpm typecheck
```

The app uses the App Router and lives under `app/`.
