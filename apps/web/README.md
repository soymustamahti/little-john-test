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

## Workspace

The workspace now contains:

- Axios handles HTTP transport
- TanStack Query owns list and mutation state
- dedicated routes for extraction templates, document categories, and uploaded documents
- a document upload flow that sends files to the API through multipart requests and then refreshes
  the catalog from React Query
- in-app document previews: PDFs and images render inline, while DOCX and spreadsheet formats are
  previewed through browser-side adapters in a modal

The frontend expects the API to be available at `http://localhost:2026` by default. Override it
with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:2026 pnpm dev
```
