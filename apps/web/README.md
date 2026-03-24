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

## Access Gate

The web app now includes a simple password gate implemented entirely in `apps/web`.

- unauthenticated requests are redirected to `/access`
- entering the correct password sets an HTTP-only cookie in the Next.js app
- `/access/logout` clears that cookie and locks the workspace again

Set `APP_ACCESS_PASSWORD` in the web deployment environment to change the password. If it is not
set, the app falls back to a built-in demo password and should be treated only as a temporary
barrier, not real authentication.

## Docker

Build the production image from the repo root so PNPM can use the workspace lockfile:

```bash
docker build -f apps/web/Dockerfile \
  --build-arg NEXT_PUBLIC_API_BASE_URL=https://api.example.com \
  -t extract-agent-web .
```

Run it with:

```bash
docker run --rm -p 3000:3000 extract-agent-web
```

`NEXT_PUBLIC_API_BASE_URL` is a build-time setting for the client bundle, so point it at the API
URL you want the browser to call before you build the image.
