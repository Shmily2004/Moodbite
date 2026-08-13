# MoodBite Frontend (Demo)

This is a minimal React + Vite demo UI to interact with the MoodBite backend API.

## Quickstart

Install and run (requires Node.js 18+ recommended):

```bash
cd frontend
npm install
npm run dev
```

Open the site at http://localhost:5173 and use the "Upload Floorplan" and "Recommend" pages.

API base is `http://localhost:8001/api` by default. Set `REACT_APP_API_BASE` when running to change.

NOTE: The Photo→3D / floorplan detection UI is intentionally paused per project
architecture decisions. The "Upload Floorplan" page in this demo only shows
an informational message and does not upload images. Do not re-enable this
feature without confirming with the project owner. See `docs/architecture_decisions.md`.
