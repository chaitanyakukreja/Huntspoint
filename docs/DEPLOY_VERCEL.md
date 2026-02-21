# Deploying on Vercel

This project can be deployed as a **static site** on Vercel. The map and layer data are served from the `public/` directory; no server-side API is required at runtime.

## Prerequisites

- Node.js (for Vercel CLI) or a Vercel account (GitHub/GitLab/Bitbucket)
- Python 3.9+ and dependencies installed (to build layers locally)

## Build steps (before deploy)

1. **Install Python dependencies** (from project root):

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Ingest and build layers** (first time or when data should be refreshed):

   ```bash
   python scripts/ingest_data.py
   python scripts/build_layers.py
   ```

   This writes `data/layers/grid_layers.geojson` and `data/layers/truck_routes.geojson`.

3. **Prepare the `public/` directory** for Vercel:

   ```bash
   bash scripts/prepare_vercel.sh
   ```

   This copies the layer GeoJSON files into `public/layers/` and ensures `public/api/bounds.json` exists.

4. **Commit** the `public/` directory (including `public/layers/*.geojson` and `public/index.html`) so Vercel can serve them.

## Vercel configuration

- **Output directory**: `public`
- **Build command**: Leave empty (static deploy; layers are pre-built).
- **Install command**: Optional; not required if you only deploy pre-built `public/`.

The repo’s `vercel.json` already sets:

- `outputDirectory`: `"public"`
- Rewrites so that:
  - `/api/layers/grid` → `/layers/grid_layers.geojson`
  - `/api/layers/truck_routes` → `/layers/truck_routes.geojson`
  - `/api/bounds` → `/api/bounds.json`

The frontend in `public/index.html` requests these URLs, so the map works without a backend.

## Deploy via Vercel dashboard

1. Push the project to GitHub (or GitLab/Bitbucket).
2. In [Vercel](https://vercel.com), import the repository.
3. Set **Root Directory** to the project root (where `vercel.json` lives).
4. Set **Output Directory** to `public` (or leave as-is if `vercel.json` is used).
5. Deploy. The site will be available at the provided URL.

## Deploy via Vercel CLI

```bash
npm i -g vercel
vercel
```

Follow the prompts; use the existing `vercel.json` so the output directory and rewrites are applied.

## Updating the live site

1. Re-run `python scripts/build_layers.py` (and optionally `scripts/ingest_data.py`) when you want fresh data.
2. Run `bash scripts/prepare_vercel.sh`.
3. Commit and push the updated `public/` (or run `vercel --prod` if using the CLI).

## Notes

- The map is client-only: all layer and bounds requests go to static files under `public/`.
- To change the map UI, edit `public/index.html` (or keep `frontend/index.html` in sync and copy it into `public/` as part of your workflow).
