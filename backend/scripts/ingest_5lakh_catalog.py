#!/usr/bin/env python3
"""Batch-ingest the fashion catalog into ChromaDB using OpenRouter embeddings.

Run from the repository root:

    uv run python backend/scripts/ingest_5lakh_catalog.py --limit 100

The script is dense-only by design. Sparse retrieval can be added later without
requiring every ingestion run to install or load a second embedding model.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import os
from pathlib import Path
from typing import Any, Literal

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

LOG = logging.getLogger("fashion_ingestion")


class CatalogRow(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        allow_inf_nan=False,
    )

    product_id: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    brand: str = Field(min_length=1)
    department: Literal["Men", "Women", "Kids", "Accessories"]
    category: Literal[
        "T-Shirt",
        "Shirt",
        "Short",
        "Pant",
        "Bags & Backpacks",
        "Watches & Jewelry",
        "Belts, Eyewear & Small Accessories",
    ]
    sub_type: str
    product_title: str = Field(min_length=1)
    material_type: str = Field(min_length=1)
    collar_or_waist_type: str
    color: str
    pattern: str
    fit_type: str
    available_sizes: str
    occasion: str
    season: str
    mrp_inr: int = Field(ge=0)
    discount_pct: int = Field(ge=0, le=100)
    selling_price_inr: int = Field(ge=0)
    in_stock: str
    overall_rating: float = Field(ge=0, le=5)
    rating_count: int = Field(ge=0)
    past_user_ratings_breakdown: str
    latest_user_review_rating: int = Field(ge=1, le=5)
    latest_user_review_text: str
    second_user_review_rating: int = Field(ge=1, le=5)
    second_user_review_text: str
    care_instructions: str
    rag_search_summary: str = Field(min_length=1)


def build_payload(row: CatalogRow, model_name: str) -> dict[str, Any]:
    """Create ChromaDB-safe primitive metadata for one catalog row."""
    payload = row.model_dump()
    payload["available_sizes"] = "|".join(
        size.strip() for size in row.available_sizes.split("|") if size.strip()
    )
    payload["past_user_reviews_json"] = json.dumps(
        [
            {
                "rating": row.latest_user_review_rating,
                "review": row.latest_user_review_text,
                "verified_buyer": False,
            },
            {
                "rating": row.second_user_review_rating,
                "review": row.second_user_review_text,
                "verified_buyer": False,
            },
        ],
        ensure_ascii=False,
    )
    payload["_embedding_model"] = model_name
    payload["_embedding_input_type"] = "search_document"
    return payload


class OpenRouterEmbedder:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float,
        max_retries: int,
    ) -> None:
        self.model = model
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout, connect=30),
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        body = {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
            "input_type": "search_document",
        }
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.post("embeddings", json=body)
                if response.status_code in {408, 429} or response.status_code >= 500:
                    response.raise_for_status()
                response.raise_for_status()
                result = response.json()
                data = result.get("data")
                if not isinstance(data, list) or len(data) != len(texts):
                    raise RuntimeError("Embedding count does not match input count")
                indices = [item.get("index") for item in data]
                if set(indices) != set(range(len(texts))):
                    raise RuntimeError("Embedding response indices are invalid")
                data.sort(key=lambda item: item["index"])
                vectors = [[float(value) for value in item["embedding"]] for item in data]
                if any(not vector for vector in vectors):
                    raise RuntimeError("OpenRouter returned an empty embedding")
                if len({len(vector) for vector in vectors}) != 1:
                    raise RuntimeError("Embedding dimensions differ within a batch")
                return vectors
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                if attempt >= self.max_retries:
                    raise RuntimeError("OpenRouter embedding retries exhausted") from exc
                delay = min(10.0, 2**attempt)
                LOG.warning("Embedding request failed; retrying in %.1fs: %s", delay, exc)
                await asyncio.sleep(delay)
        raise RuntimeError("OpenRouter embedding retries exhausted")


def save_checkpoint(path: Path, row_number: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps({"last_committed_row": row_number}), encoding="utf-8")
    temporary.replace(path)


def load_checkpoint(path: Path, restart: bool) -> int:
    if restart or not path.exists():
        return 0
    state = json.loads(path.read_text(encoding="utf-8"))
    return int(state.get("last_committed_row", 0))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=PROJECT_ROOT / "data" / "fashion_catalog_5lakh.csv")
    parser.add_argument("--checkpoint", type=Path, default=PROJECT_ROOT / "backend/.ingestion/catalog.checkpoint.json")
    parser.add_argument("--batch-size", type=int, default=int(os.getenv("INGEST_BATCH_SIZE", "16")))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--restart", action="store_true")
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")
    if args.batch_size > 500:
        parser.error("--batch-size must not exceed 500")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    return args


async def run(args: argparse.Namespace) -> None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_api_key":
        raise RuntimeError("Set OPENROUTER_API_KEY in .env before ingesting")
    if not args.csv.is_file():
        raise FileNotFoundError(args.csv)

    model_name = os.getenv("EMBEDDING_MODEL", "nvidia/nemotron-3-embed-1b:free")
    import chromadb

    persist_dir = Path(
        os.getenv("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "data/vector_indices/chroma"))
    )
    collection_name = os.getenv("CHROMA_PRODUCT_COLLECTION", "fashion_catalog_5lakh")
    chroma = chromadb.PersistentClient(path=str(persist_dir))
    collection = chroma.get_or_create_collection(
        name=collection_name,
        configuration={"hnsw": {"space": "cosine"}},
        metadata={"embedding_model": model_name},
    )
    embedder = OpenRouterEmbedder(
        api_key=api_key,
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        model=model_name,
        timeout=float(os.getenv("INGEST_HTTP_TIMEOUT_SECONDS", "180")),
        max_retries=3,
    )
    committed_row = load_checkpoint(args.checkpoint, args.restart)
    processed = 0
    selected = 0

    try:
        batch: list[tuple[int, CatalogRow]] = []

        async def flush() -> None:
            nonlocal processed
            if not batch:
                return
            vectors = await embedder.embed([row.rag_search_summary for _, row in batch])
            collection.upsert(
                ids=[row.product_id for _, row in batch],
                embeddings=vectors,
                documents=[row.rag_search_summary for _, row in batch],
                metadatas=[build_payload(row, model_name) for _, row in batch],
            )
            save_checkpoint(args.checkpoint, batch[-1][0])
            processed += len(batch)
            LOG.info("Committed row %s (%s rows this run)", batch[-1][0], processed)
            batch.clear()

        with args.csv.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            required = set(CatalogRow.model_fields)
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise RuntimeError(f"Missing CSV columns: {sorted(missing)}")

            for row_number, raw in enumerate(reader, start=1):
                if row_number <= committed_row:
                    continue
                if args.limit is not None and selected >= args.limit:
                    break
                try:
                    row = CatalogRow.model_validate(raw)
                except ValidationError as exc:
                    raise RuntimeError(f"Invalid catalog row {row_number}: {exc}") from exc
                if row.selling_price_inr > row.mrp_inr:
                    raise RuntimeError(f"Selling price exceeds MRP at row {row_number}")
                batch.append((row_number, row))
                selected += 1
                if len(batch) >= args.batch_size:
                    await flush()
            await flush()
    finally:
        await embedder.close()

    LOG.info("Finished; indexed %s rows", processed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        asyncio.run(run(parse_args()))
    except KeyboardInterrupt:
        LOG.warning("Interrupted; rerun the same command to resume")
        raise SystemExit(130)
    except Exception:
        LOG.exception("Ingestion failed")
        raise SystemExit(1)
