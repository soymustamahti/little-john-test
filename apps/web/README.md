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

## Template Workspace

The home page now contains the template CRUD workspace:

- Axios handles HTTP transport
- TanStack Query owns list and mutation state
- the page is split into catalog, editor, and live structure preview panels

The frontend expects the API to be available at `http://localhost:2026` by default. Override it
with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:2026 pnpm dev
```

## Docker

Build the production image from the repo root so PNPM can use the workspace lockfile:

```bash
docker build -f apps/web/Dockerfile \
  --build-arg NEXT_PUBLIC_API_BASE_URL=https://api.example.com \
  -t little-john-web .
```

Run it with:

```bash
docker run --rm -p 3000:3000 little-john-web
```

`NEXT_PUBLIC_API_BASE_URL` is a build-time setting for the client bundle, so point it at the API
URL you want the browser to call before you build the image.
