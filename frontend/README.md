# Threadline frontend

React + TypeScript frontend for the Fashion RAG API.

## Run locally

```bash
npm install
npm run dev
```

The app expects the backend at `http://localhost:8000`. Override it with:

```bash
VITE_API_URL=http://localhost:8000 npm run dev
```

Start the backend separately:

```bash
cd ../backend
uv run uvicorn backend.app.main:app --app-dir src --reload
```
