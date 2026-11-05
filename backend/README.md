## Fashion RAG backend

This package currently provides the first runnable API slice:

- strict Pydantic request and product schemas
- deterministic catalog filtering and lexical/rating ranking over the supplied CSV
- bounded filter relaxation when strict secondary filters return fewer than two products
- defensive parsing for future OpenRouter structured responses
- liveness/readiness and product lookup endpoints

Run the API from the repository root:

```bash
cd backend
uv run uvicorn backend.app.main:app --app-dir src --reload
```

Useful checks:

```bash
PYTHONPATH=src uv run python -m py_compile $(find src tests -name '*.py' -print)
PYTHONPATH=src uv run --with pytest pytest -q
```

The current local retriever is intentionally dependency-light. OpenRouter,
ChromaDB/FAISS, Redis, SSE streaming, and offline embedding ingestion remain
the next integration slices described in `../docs/fashion_rag_production_docs.md`.