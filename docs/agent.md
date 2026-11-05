# AGENT.md — Unbreakable Hybrid Agentic RAG Engineering & Execution Guide

## 1. Mission & System Identity
You are an elite, fault-tolerant **Full-Stack AI Systems Engineer & Hybrid RAG Architect** working on the **Fashion E-Commerce Hybrid RAG Platform** (500,000 SKUs across **Men, Women, Kids, and Accessories**).

Your objective is twofold:
1. **Write Simple, Modular, Unbreakable Code**: Every backend module (FastAPI + LangChain + LangGraph), vector store adapter (ChromaDB / FAISS), and frontend component (React + TypeScript) must degrade gracefully, validate every boundary with Pydantic v2 / TypeScript, and never crash on malformed LLM outputs, empty retrievals, or free-tier API rate limits.
2. **Enforce Hybrid Agentic RAG Best Practices**: Combine **Structured Metadata Pre-Filtering** + **Dense Vector Search (`nvidia/nemotron-3-embed-1b:free`)** + **Lexical Keyword Matching (BM25)** + **Past User Review Grading** + **Self-Correcting Filter Relaxation**.

## 2. Core Tech Stack & Locked Free-Tier Resources

| Layer | Technology / Model | Strict Rule |
| :--- | :--- | :--- |
| **LLM / Vision-Language** | `nvidia/nemotron-3.5-super-vl:free` via OpenRouter | Always call through `https://openrouter.ai/api/v1` with `max_retries=3`, timeout `45s`, and JSON-extraction regex fallback |
| **Embeddings** | `nvidia/nemotron-3-embed-1b:free` via OpenRouter | Always set `check_embedding_ctx_length=False` and batch documents in chunks of `<= 500` |
| **Primary Vector Store** | **ChromaDB** (`chromadb` + `langchain-chroma`) | Store primitive metadata only (`str`, `int`, `float`, `bool`); serialize nested lists (`past_user_reviews`) as JSON strings |
| **Secondary Vector Store** | **FAISS** (`faiss-cpu`) | Always over-fetch (`fetch_k = k * 10`) when using callable metadata filters so post-filtering never starves results |
| **Orchestration** | **LangGraph** (`StateGraph`) + **LangChain Core** | Keep every graph node a pure, idempotent `async def` function returning a partial state `dict` |
| **Backend API** | **FastAPI** + **Pydantic v2** + **Redis** | Use Server-Sent Events (`text/event-stream`) for token & product-card streaming; cache repeated queries in Redis |
| **Frontend UI** | **React 18** + **TypeScript** + **Tailwind CSS** | Guard SSE stream parsing in `try / catch` blocks; render product cards independently of text stream completion |

## 3. Golden Rules for Writing "Unbreakable" Hybrid RAG Code

### Rule 1: Never Trust Raw LLM JSON Output (Defensive Parsing)
Free-tier and open-weights models (`nvidia/nemotron-3.5-super-vl:free`) may wrap JSON inside Markdown fences (` ```json ... ``` `) or add conversational preamble.
- **DO NOT** call `json.loads(response.content)` directly without sanitization.
- **ALWAYS** use a defensive extraction helper with a safe fallback default:

```python
import json
import re
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

def safe_parse_llm_json(raw_text: str, schema: Type[T], default_instance: T) -> T:
    """Extracts JSON object from LLM text safely and validates with Pydantic v2."""
    if not raw_text:
        return default_instance
    try:
        # Strip markdown fences or surrounding prose
        match = re.search(r"\{.*\}", str(raw_text), re.DOTALL)
        payload: Dict[str, Any] = json.loads(match.group(0)) if match else json.loads(str(raw_text))
        # Drop null values that violate strict Literal enums
        clean_payload = {k: v for k, v in payload.items() if v is not None and v != "null"}
        return schema.model_validate(clean_payload)
    except (json.JSONDecodeError, ValidationError, AttributeError):
        return default_instance
```

### Rule 2: True Hybrid Retrieval (Dense + BM25 Keyword + Metadata Pre-Filter)
Pure vector search struggles with exact SKU codes (`SKU-MEN-SHIRT-000142`), specific fabric weights (`13oz Raw Selvedge Denim`), or exact collar names (`Cuban Camp Collar`).
- **Step A (Metadata Filter)**: Narrow the 5-lakh catalog by exact categorical/numeric bounds (`department`, `category`, `selling_price_inr <= max_price`, `overall_rating >= min_rating`).
- **Step B (Dense Semantic Search)**: Retrieve top $K=25$ candidates using `nvidia/nemotron-3-embed-1b:free`.
- **Step C (Lexical + Review Boost)**: Apply Reciprocal Rank Fusion (RRF) or deterministic keyword scoring across `product_title`, `material_type`, `collar_or_waist_type`, and `past_user_reviews` so exact fabric/collar matches and highly rated buyer reviews always rank at the top.

```python
def compute_hybrid_score(
    vector_score: float,
    query: str,
    title: str,
    material: str,
    collar: str,
    rating: float,
    reviews_text: str,
) -> float:
    """Combines dense similarity with exact lexical match and verified buyer rating."""
    q_tokens = {tok for tok in query.lower().split() if len(tok) > 2}
    if not q_tokens:
        return vector_score

    field_blob = f"{title} {material} {collar}".lower()
    lexical_hits = sum(1 for tok in q_tokens if tok in field_blob)
    review_hits = sum(1 for tok in q_tokens if tok in reviews_text.lower())

    lexical_boost = (lexical_hits / len(q_tokens)) * 0.20
    review_boost = min(review_hits * 0.04, 0.12)
    rating_boost = max((rating - 3.5) * 0.05, 0.0)

    return round(vector_score + lexical_boost + review_boost + rating_boost, 4)
```

### Rule 3: Zero-Dead-End Retrieval (Automatic Filter Relaxation Circuit)
When a user asks for an ultra-specific combination (e.g., *"Kids velvet tuxedo shirt under ₹400 with 4.8+ rating"*), strict metadata filtering might return `0` items.
- **Unbreakable Pattern**: Never return an empty list on the first miss. Route through a bounded **2-stage relaxation loop** in LangGraph:
  1. **Attempt 1 (Strict)**: Apply all extracted filters (`department`, `category`, `material_type`, `collar_or_waist_type`, `max_price_inr`, `min_rating`).
  2. **Attempt 2 (Relaxed Secondary Attributes)**: If `len(results) < 2`, drop `collar_or_waist_type` and `material_type` from the hard `where` filter (keeping them in the semantic vector query) and widen `max_price_inr` by `+20%`.
  3. **Attempt 3 (Department + Category Fallback)**: If still empty, filter only by `department` and `category` and let semantic + lexical scoring rank the closest alternatives, setting `filter_relaxed=True` so the UI informs the user transparently.

### Rule 4: OpenRouter Free-Tier Rate-Limit & Timeout Resilience
OpenRouter `:free` endpoints enforce per-minute request quotas and can experience brief latency spikes.
- **Exponential Backoff**: Wrap all embedding and LLM calls with `tenacity` (`wait_exponential(multiplier=1, min=2, max=10)`, `stop_after_attempt(3)`).
- **Graceful Degradation (Catalog-Only Fallback)**: If the LLM generation node (`generate_answer`) times out or hits a `429 Too Many Requests` error after retries, **do not fail the HTTP request**. The SSE stream has *already* delivered the ranked `products` array to React—emit a clean deterministic summary string built from the top 3 matched SKUs (`product_title`, `material_type`, `selling_price_inr`, and `overall_rating`) and close the stream cleanly with `data: [DONE]`.

```python
from langchain_core.messages import HumanMessage, SystemMessage
from app.schemas.chat import ProductCardResponse

async def safe_generate_stylist_answer(llm, system_prompt: str, user_query: str, products: list[ProductCardResponse]) -> str:
    """Calls OpenRouter LLM with a deterministic template fallback if the free API is rate-limited."""
    try:
        resp = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query),
        ])
        return str(resp.content)
    except Exception:
        if not products:
            return "We couldn't find an exact match for those filters. Try broadening your price range or material preference."
        top = products[0]
        return (
            f"Based on your search, our top recommendation is the **{top.product_title}** "
            f"(crafted from {top.material_type}, {top.collar_or_waist_type}) priced at **₹{top.selling_price_inr}** "
            f"with a **{top.overall_rating}/5.0** rating across {top.rating_count} buyer reviews."
        )
```

### Rule 5: ChromaDB & FAISS Metadata Safety Constraints
- **ChromaDB Flat Metadata Rule**: ChromaDB raises a runtime `ValueError` if any metadata field is a `list`, `dict`, or `None`.
  - Always convert `None` to `""` or `0` during ingestion.
  - Keep `available_sizes` as a pipe-delimited string (`"S|M|L|XL"`) and `past_user_reviews_json` as a serialized JSON string in ChromaDB metadata, then deserialize inside the Pydantic mapper.
  - In ChromaDB `where` filters, whenever 2 or more field conditions exist, wrap them inside `{"$and": [cond1, cond2, ...]}` (ChromaDB rejects multi-key top-level dictionaries without `$and` / `$or`).

## 4. LangGraph Hybrid Agent Workflow Specification

Every feature addition or modification to `backend/app/rag/` must preserve this 5-node state machine:

```text
[START]
   │
   ▼
┌──────────────────────────────────────────────────────────┐
│ Node 1: parse_query_and_filters_node                     │
│ • Model: nvidia/nemotron-3.5-super-vl:free               │
│ • Parses text + optional image_url via safe_parse_llm_json│
│ • Merges explicit UI facets over LLM-inferred filters    │
└──────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────┐
│ Node 2: hybrid_retrieve_node                             │
│ • Model: nvidia/nemotron-3-embed-1b:free                 │
│ • Queries ChromaDB ($and filter) or FAISS (over-fetched) │
│ • Retrieves top K=25 SKUs + Domain KB markdown rules     │
└──────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────┐
│ Node 3: grade_and_rerank_node                            │
│ • Computes compute_hybrid_score (Vector + BM25 + Reviews)│
│ • Filters out low-relevance items and selects top N=6    │
└──────────────────────────────────────────────────────────┘
   │
   ├─── If len(reranked_products) < 2 and not filter_relaxed ───► [Node 3B: relax_filters_node] ──┐
   │                                                                                              │
   │◄─────────────────────────────────────────────────────────────────────────────────────────────┘
   ▼
┌──────────────────────────────────────────────────────────┐
│ Node 4: generate_stylist_answer_node                     │
│ • Model: nvidia/nemotron-3.5-super-vl:free               │
│ • Streams grounded styling advice citing SKU IDs,        │
│   materials, collars, prices & verbatim buyer reviews    │
│ • Protected by safe_generate_stylist_answer fallback     │
└──────────────────────────────────────────────────────────┘
   │
   ▼
 [END]
```

## 5. Step-by-Step Task Execution Protocol for the Coding Agent

Whenever you are asked to implement, debug, or extend a feature in this repository, follow this exact checklist:

1. **Inspect Schemas First (`backend/app/schemas/` & `frontend/src/types/`)**:
   - Verify that any new field (e.g., `season`, `occasion`, `discount_pct`) is added to both the FastAPI Pydantic v2 model and the React TypeScript interface before touching business logic.
2. **Keep Functions Small & Pure (< 50 Lines per Function)**:
   - Separate I/O clients (`db/vector_store.py`, `rag/openrouter.py`) from data transformation (`rag/retriever.py`, `rag/reranker.py`) so every function can be unit-tested without live network calls.
3. **Validate Vector Filter Syntax Before Running**:
   - Test ChromaDB `where` dictionaries against single-filter (`{"department": {"$eq": "Men"}}`) and multi-filter (`{"$and": [...]}`) cases.
4. **Verify Groundedness (Zero Hallucinated SKUs)**:
   - System prompts must explicitly instruct the model: *"Never invent product names, prices, or SKU IDs. Only recommend items present in `Retrieved Products`."*
5. **Run Verification Checks Before Completing Any Task**:
   - Run `python -m py_compile` on all modified Python files.
   - Verify FastAPI OpenAPI schema generation (`python -c "from app.main import app; print(len(app.routes))"`).
   - Verify TypeScript compilation (`npm run build` or `tsc --noEmit`) on frontend changes.
