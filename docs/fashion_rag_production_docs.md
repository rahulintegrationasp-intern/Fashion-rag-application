# Production Technical Documentation: Fashion E-Commerce RAG Platform (100% Free-Tier Stack)

**Stack:** React 18 (TypeScript + Tailwind + TanStack Query) | FastAPI (Python 3.11 + Asyncio + Pydantic v2) | LangChain & LangGraph (Stateful Agentic RAG) | **OpenRouter Free AI (`nvidia/nemotron-3.5-super-vl:free`) & Free Embeddings (`nvidia/nemotron-3-embed-1b:free`)** | **ChromaDB / FAISS (Open-Source Vector Stores)** | Redis (Semantic Cache & Session Memory)

## 1. End-to-End Free-Tier RAG Workflow (Step-by-Step Process)

The platform processes **500,000 (5 Lakh) structured catalog SKUs** (`fashion_catalog_5lakh.csv` / `fashion_rag_chunks_10k.jsonl`) and **domain styling rules** (`fashion_knowledge_base_rag.md`) using zero-cost, open-source vector stores (**ChromaDB** or **FAISS**) and free-tier OpenRouter NVIDIA Nemotron models.

### Phase A: Offline Data Ingestion & Indexing Pipeline
1. **Step 1 — Data Validation & Normalization**: Streams `fashion_catalog_5lakh.csv` (500,000 rows) in batches using Pydantic v2 schemas to validate `department` (`Men`, `Women`, `Kids`, `Accessories`), `category` (`T-Shirt`, `Shirt`, `Short`, `Pant`, etc.), `material_type`, `collar_or_waist_type`, `selling_price_inr`, `overall_rating`, and verbatim buyer reviews.
2. **Step 2 — Dual Document Preparation**:
   - **Catalog Vector Payloads**: Uses `rag_search_summary` as the semantic document text while attaching all structured attributes (`department`, `category`, `material_type`, `collar_or_waist_type`, `color`, `available_sizes`, `selling_price_inr`, `overall_rating`, `rating_count`, `past_user_ratings_breakdown`) as filterable metadata.
   - **Knowledge Base Chunking**: Splits `fashion_knowledge_base_rag.md` using `MarkdownHeaderTextSplitter` into a dedicated `fashion_domain_kb` ChromaDB collection / FAISS index.
3. **Step 3 — OpenRouter Free Embedding Generation (`nvidia/nemotron-3-embed-1b:free`)**: Calls OpenRouter's OpenAI-compatible Embeddings endpoint (`https://openrouter.ai/api/v1/embeddings`) with model `nvidia/nemotron-3-embed-1b:free` to encode dense semantic representations of product descriptions, material compositions, collar types, and buyer reviews.
4. **Step 4 — Vector Store Indexing (ChromaDB or FAISS)**:
   - **Option A — ChromaDB (Recommended for Metadata Filtering)**: Persists embeddings and rich JSON metadata in a local/Dockerized ChromaDB server (`chromadb/chroma`), enabling compound `$and` pre-filters (`department == "Men"`, `selling_price_inr <= 2500`, `overall_rating >= 4.2`) alongside HNSW cosine similarity search.
   - **Option B — FAISS (Recommended for Ultra-Fast In-Memory ANN on 5 Lakh Rows)**: Stores normalized vectors in a partitioned `IndexIVFFlat` or `IndexHNSWFlat` FAISS index on disk with a synchronized SQLite/in-memory metadata dictionary for post-filter or ID-selector filtering.

### Phase B: Online Runtime Request Lifecycle (React -> FastAPI -> LangGraph -> OpenRouter)
1. **Step 5 — User Query / Visual Input & UI Filter Dispatch (React)**: The user submits a text query (e.g., *"Show me breathable linen mandarin-collar shirts for men under ₹2,500 with a 4.3+ rating"*) or an optional outfit reference image URL (supported natively by `nvidia/nemotron-3.5-super-vl:free`) to `POST /api/v1/chat/stream`.
2. **Step 6 — Gateway Auth, Rate Limiting & Semantic Cache Check (FastAPI + Redis)**:
   - FastAPI validates the request via Pydantic v2, enforces rate limits, and checks **Redis Semantic Cache** so repeated queries return in $<10\text{ ms}$ without consuming OpenRouter free-tier rate limits.
3. **Step 7 — Node 1: Multimodal Intent & Self-Query Metadata Parser (`nvidia/nemotron-3.5-super-vl:free`)**:
   - If the user attached a photo of a garment, `nvidia/nemotron-3.5-super-vl:free` inspects the visual attributes (collar cut, fabric texture, pattern, color) and combines them with the text prompt.
   - Extracts structured filters (`department`, `category`, `material_type`, `collar_or_waist_type`, `color`, `max_price_inr`, `min_rating`) and a clean `semantic_query`.
4. **Step 8 — Node 2: Filtered Vector Retrieval (ChromaDB / FAISS + `nvidia/nemotron-3-embed-1b:free`)**:
   - Embeds `semantic_query` using `nvidia/nemotron-3-embed-1b:free` and queries ChromaDB (using `where` metadata operators) or FAISS (using metadata predicate filtering) to retrieve the top $K=25$ candidate SKUs, plus domain rules from `fashion_domain_kb`.
5. **Step 9 — Node 3: Past Buyer Review Grader & Reranker (LangGraph)**:
   - Scores the 25 candidates down to the top $N=6$ products by evaluating how well each SKU's `latest_user_review_text` and `second_user_review_text` satisfy the user's durability, sizing, or comfort requirements.
   - **Conditional Edge (Self-Correction)**: If fewer than 2 products match, LangGraph routes to the **Filter Relaxation Node** (relaxing collar/pattern constraints or expanding budget by +20%) and re-queries ChromaDB/FAISS automatically.
6. **Step 10 — Node 4: Grounded Stylist Synthesis & SSE Streaming (`nvidia/nemotron-3.5-super-vl:free`)**:
   - Streams the conversational recommendation token-by-token via Server-Sent Events (SSE) alongside structured JSON product cards (`product_id`, `sku`, `material_type`, `collar_or_waist_type`, `selling_price_inr`, `overall_rating`, `past_user_ratings_breakdown`, and verbatim buyer reviews).

## 2. Production Monorepo File & Directory Structure

```text
fashion-rag-platform/
├── docker-compose.yml                  # Orchestrates FastAPI, React, ChromaDB, Redis
├── .env.example                        # OpenRouter API key & ChromaDB/FAISS settings
├── Makefile                            # Developer commands (make ingest-chroma, make ingest-faiss, make dev)
├── data/
│   ├── fashion_catalog_5lakh.csv       # 500,000 synthetic SKU catalog
│   ├── fashion_rag_chunks_10k.jsonl    # 10,000 pre-chunked JSONL sample
│   ├── fashion_knowledge_base_rag.md   # Domain styling & material care guide
│   └── vector_indices/                 # Local persistence for ChromaDB SQLite/HNSW & FAISS .index files
│
├── backend/                            # FastAPI + LangChain + LangGraph Service
│   ├── Dockerfile
│   ├── pyproject.toml                  # Dependencies (fastapi, langgraph, langchain-openai, chromadb, faiss-cpu, redis)
│   ├── scripts/
│   │   └── ingest_5lakh_catalog.py     # Batch ingestion script supporting both ChromaDB and FAISS
│   └── app/
│       ├── main.py                     # FastAPI application entrypoint & lifespan hooks
│       ├── core/
│       │   ├── config.py               # Pydantic BaseSettings (OpenRouter URLs, Models, Chroma/FAISS toggle)
│       │   ├── logging.py              # Structured JSON logging
│       │   ├── security.py             # JWT authentication & rate limiting
│       │   └── exceptions.py           # Global exception & OpenRouter retry handlers
│       ├── db/
│       │   ├── vector_store.py         # Unified ChromaDB & FAISS client manager
│       │   └── redis.py                # Async Redis client for semantic cache & chat history
│       ├── schemas/
│       │   ├── product.py              # Product SKU, ReviewBreakdown, FilterFacet schemas
│       │   ├── chat.py                 # ChatQueryRequest (text + optional image_url), ProductCardResponse
│       │   └── feedback.py             # User thumbs-up/down & citation click tracking
│       ├── rag/                        # LangChain & LangGraph Core Engine
│       │   ├── state.py                # LangGraph TypedDict State definition
│       │   ├── openrouter.py           # OpenRouter ChatOpenAI (nemotron-3.5-super-vl:free) & Embeddings (nemotron-3-embed-1b:free)
│       │   ├── retriever.py            # Dual ChromaDB ($and where filter) & FAISS retriever implementation
│       │   ├── reranker.py             # Review relevance scoring & lightweight reranker
│       │   ├── nodes.py                # LangGraph nodes (parse_query, retrieve, grade, relax, generate)
│       │   └── graph.py                # Compiled StateGraph workflow
│       └── api/
│           ├── deps.py                 # FastAPI Dependency Injection
│           └── v1/
│               ├── router.py           # Aggregates all v1 API routers
│               └── endpoints/
│                   ├── chat.py         # POST /chat/stream (SSE) & POST /chat/query
│                   ├── search.py       # POST /search/hybrid (Direct ChromaDB/FAISS search)
│                   ├── products.py     # GET /products/{product_id} & similar items
│                   ├── ingest.py       # POST /ingest/batch (Background catalog indexing)
│                   └── health.py       # GET /health/live & GET /health/ready
│
└── frontend/                           # React 18 + TypeScript + Vite + Tailwind CSS
    ├── Dockerfile
    ├── package.json
    ├── tsconfig.json
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── types/
        │   └── rag.ts                  # TypeScript interfaces matching FastAPI Pydantic schemas
        ├── api/
        │   ├── client.ts               # Axios instance + SSE stream helper
        │   └── ragApi.ts               # API functions for text/visual chat stream & facet search
        ├── hooks/
        │   ├── useRagStream.ts         # Custom React hook for SSE token streaming & product cards
        │   └── useCatalogFilters.ts    # State management for Men/Women/Kids/Accessories facets
        ├── components/
        │   ├── chat/
        │   │   ├── ChatSidebar.tsx     # AI Fashion Stylist chat + Image Upload for Super-VL visual search
        │   │   ├── MessageBubble.tsx   # Renders streamed Markdown + grounded citations
        │   │   └── ActiveFilterPills.tsx # Displays LLM-inferred metadata filters (material, collar, rating)
        │   └── catalog/
        │       ├── ProductCard.tsx     # Displays SKU, material, collar, price, star breakdown & past reviews
        │       ├── ReviewDrawer.tsx    # Expandable modal showing verified buyer reviews & 5-star bar chart
        │       └── FacetFilterBar.tsx  # Department, Category, Material, Collar, and Rating sliders
        └── pages/
            └── StorefrontPage.tsx      # Unified Search + AI Stylist + Product Grid view
```

## 3. Production API Specification (FastAPI Endpoints)

| Method | Endpoint | Description | Underlying Free-Tier Service |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/chat/stream` | Streams LangGraph node events, inferred filters, matched product cards, and LLM tokens over **SSE** (supports text + optional `image_url`) | `nvidia/nemotron-3.5-super-vl:free` + ChromaDB/FAISS |
| `POST` | `/api/v1/chat/query` | Synchronous JSON endpoint returning the complete stylist answer, inferred metadata filters, and ranked product cards | `nvidia/nemotron-3.5-super-vl:free` + ChromaDB/FAISS |
| `POST` | `/api/v1/search/hybrid` | Direct vector + metadata search without LLM generation for instant catalog grid filtering | `nvidia/nemotron-3-embed-1b:free` + ChromaDB/FAISS |
| `GET` | `/api/v1/products/{product_id}` | Fetches full SKU metadata, size availability, care instructions, and past user review breakdown | ChromaDB / FAISS Metadata Store |
| `GET` | `/api/v1/products/{product_id}/similar` | Finds visually and semantically similar items ("Complete the Look") via vector nearest neighbors | ChromaDB / FAISS HNSW Search |
| `POST` | `/api/v1/ingest/batch` | Background task to index CSV/JSONL catalog batches into ChromaDB or FAISS | `nvidia/nemotron-3-embed-1b:free` |
| `GET` | `/api/v1/health/ready` | Readiness probe checking ChromaDB heartbeat / FAISS index load, Redis ping, and OpenRouter status | FastAPI Health Check |

## 4. Backend Implementation (FastAPI + OpenRouter + ChromaDB / FAISS + LangGraph)

### 4.1 Configuration & Environment (`backend/app/core/config.py`)

```python
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Fashion E-Commerce RAG API (Free-Tier Stack)"
    SITE_URL: str = "https://fashion-rag.example.com"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "production"

    # OpenRouter Free Models Configuration
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    EMBEDDING_MODEL: str = "nvidia/nemotron-3-embed-1b:free"
    LLM_MODEL: str = "nvidia/nemotron-3.5-super-vl:free"

    # Vector Store Selection: "chromadb" or "faiss"
    VECTOR_STORE_TYPE: Literal["chromadb", "faiss"] = "chromadb"

    # ChromaDB Configuration (Client-Server or Persistent Local)
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    CHROMA_PERSIST_DIR: str = "./data/vector_indices/chroma"
    CHROMA_PRODUCT_COLLECTION: str = "fashion_catalog_5lakh"
    CHROMA_KB_COLLECTION: str = "fashion_domain_kb"

    # FAISS Configuration (Local Disk Persistence)
    FAISS_INDEX_DIR: str = "./data/vector_indices/faiss_catalog"
    FAISS_KB_INDEX_DIR: str = "./data/vector_indices/faiss_kb"

    # Redis (Semantic Cache & Rate Limit Counter)
    REDIS_URL: str = "redis://redis:6379/0"
    CACHE_TTL_SECONDS: int = 3600

    TOP_K_RETRIEVAL: int = 25
    TOP_N_RERANK: int = 6

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
```

### 4.2 OpenRouter LLM & Embedding Factory (`backend/app/rag/openrouter.py`)

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.core.config import settings

def get_openrouter_embeddings() -> OpenAIEmbeddings:
    """
    Initializes OpenRouter's free NVIDIA Nemotron 1B Embedding model
    (nvidia/nemotron-3-embed-1b:free) via the OpenAI-compatible endpoint.
    """
    return OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base=settings.OPENROUTER_BASE_URL,
        check_embedding_ctx_length=False,
        default_headers={
            "HTTP-Referer": settings.SITE_URL,
            "X-Title": settings.PROJECT_NAME,
        },
    )

def get_openrouter_llm(streaming: bool = True, temperature: float = 0.1) -> ChatOpenAI:
    """
    Initializes OpenRouter's free NVIDIA Nemotron 3.5 Super VL model
    (nvidia/nemotron-3.5-super-vl:free) supporting both text and visual garment queries.
    """
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=temperature,
        streaming=streaming,
        max_retries=3,
        default_headers={
            "HTTP-Referer": settings.SITE_URL,
            "X-Title": settings.PROJECT_NAME,
        },
    )

embeddings_model = get_openrouter_embeddings()
chat_llm = get_openrouter_llm(streaming=True)
parser_llm = get_openrouter_llm(streaming=False, temperature=0.0)
```

### 4.3 Pydantic v2 Schemas (`backend/app/schemas/chat.py`)

```python
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class UserReviewItem(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Star rating from past buyer")
    review: str = Field(..., description="Verbatim past user review text")
    verified_buyer: bool = True

class CatalogFilterSchema(BaseModel):
    department: Optional[Literal["Men", "Women", "Kids", "Accessories"]] = None
    category: Optional[Literal[
        "T-Shirt", "Shirt", "Short", "Pant",
        "Bags & Backpacks", "Watches & Jewelry", "Belts, Eyewear & Small Accessories"
    ]] = None
    material_type: Optional[str] = Field(None, description="e.g., 100% European Linen, Supima Cotton")
    collar_or_waist_type: Optional[str] = Field(None, description="e.g., Mandarin Band Collar, Crew Neck, Polo Collar")
    color: Optional[str] = None
    fit_type: Optional[str] = None
    max_price_inr: Optional[int] = Field(None, ge=0, le=500000)
    min_rating: Optional[float] = Field(None, ge=1.0, le=5.0)

class ProductCardResponse(BaseModel):
    product_id: str
    sku: str
    brand: str
    department: str
    category: str
    sub_type: str
    product_title: str
    material_type: str
    collar_or_waist_type: str
    color: str
    pattern: str
    fit_type: str
    available_sizes: List[str]
    mrp_inr: int
    discount_pct: int
    selling_price_inr: int
    overall_rating: float
    rating_count: int
    past_user_ratings_breakdown: str
    past_user_reviews: List[UserReviewItem]
    care_instructions: str
    relevance_score: float

class ChatQueryRequest(BaseModel):
    session_id: str = Field(..., description="Unique conversation thread ID")
    query: str = Field(..., min_length=2, max_length=1000)
    image_url: Optional[str] = Field(
        None,
        description="Optional garment/outfit image URL analyzed by nvidia/nemotron-3.5-super-vl:free"
    )
    explicit_filters: Optional[CatalogFilterSchema] = None

class ChatQueryResponse(BaseModel):
    session_id: str
    answer: str
    inferred_filters: CatalogFilterSchema
    products: List[ProductCardResponse]
    filter_relaxed: bool = False
```

### 4.4 Dual Vector Store Retriever: ChromaDB & FAISS (`backend/app/rag/retriever.py`)

```python
import json
from typing import Any, Dict, List, Optional
import chromadb
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from app.core.config import settings
from app.rag.openrouter import embeddings_model
from app.schemas.chat import CatalogFilterSchema, ProductCardResponse, UserReviewItem

# ---------------------------------------------------------------------------
# 1. ChromaDB Filter Builder ($and compound where clause)
# ---------------------------------------------------------------------------
def build_chroma_where_filter(f: CatalogFilterSchema) -> Optional[Dict[str, Any]]:
    conditions: List[Dict[str, Any]] = []
    if f.department:
        conditions.append({"department": {"$eq": f.department}})
    if f.category:
        conditions.append({"category": {"$eq": f.category}})
    if f.color:
        conditions.append({"color": {"$eq": f.color}})
    if f.fit_type:
        conditions.append({"fit_type": {"$eq": f.fit_type}})
    if f.max_price_inr is not None:
        conditions.append({"selling_price_inr": {"$lte": f.max_price_inr}})
    if f.min_rating is not None:
        conditions.append({"overall_rating": {"$gte": f.min_rating}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}

# ---------------------------------------------------------------------------
# 2. FAISS Callable Metadata Filter Predicate
# ---------------------------------------------------------------------------
def build_faiss_filter_callable(f: CatalogFilterSchema):
    def _predicate(metadata: Dict[str, Any]) -> bool:
        if f.department and metadata.get("department") != f.department:
            return False
        if f.category and metadata.get("category") != f.category:
            return False
        if f.material_type and f.material_type.lower() not in metadata.get("material_type", "").lower():
            return False
        if f.collar_or_waist_type and f.collar_or_waist_type.lower() not in metadata.get("collar_or_waist_type", "").lower():
            return False
        if f.color and f.color.lower() not in metadata.get("color", "").lower():
            return False
        if f.max_price_inr is not None and int(metadata.get("selling_price_inr", 0)) > f.max_price_inr:
            return False
        if f.min_rating is not None and float(metadata.get("overall_rating", 0.0)) < f.min_rating:
            return False
        return True
    return _predicate

# ---------------------------------------------------------------------------
# 3. Singleton Loaders for ChromaDB and FAISS
# ---------------------------------------------------------------------------
_chroma_store: Optional[Chroma] = None
_faiss_store: Optional[FAISS] = None

def get_chroma_vectorstore() -> Chroma:
    global _chroma_store
    if _chroma_store is None:
        client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        _chroma_store = Chroma(
            client=client,
            collection_name=settings.CHROMA_PRODUCT_COLLECTION,
            embedding_function=embeddings_model,
        )
    return _chroma_store

def get_faiss_vectorstore() -> FAISS:
    global _faiss_store
    if _faiss_store is None:
        _faiss_store = FAISS.load_local(
            folder_path=settings.FAISS_INDEX_DIR,
            embeddings=embeddings_model,
            allow_dangerous_deserialization=True,
        )
    return _faiss_store

# ---------------------------------------------------------------------------
# 4. Unified Retrieval Function (Supports both ChromaDB and FAISS)
# ---------------------------------------------------------------------------
async def execute_vector_search(
    query_text: str,
    filters: CatalogFilterSchema,
    top_k: int = 25
) -> List[ProductCardResponse]:
    if settings.VECTOR_STORE_TYPE == "chromadb":
        store = get_chroma_vectorstore()
        where_clause = build_chroma_where_filter(filters)
        # Optional substring filter on document text for material or collar
        where_doc = None
        if filters.material_type:
            where_doc = {"$contains": filters.material_type}

        docs_and_scores = await store.asimilarity_search_with_relevance_scores(
            query=query_text,
            k=top_k,
            filter=where_clause,
            where_document=where_doc,
        )
    else:
        # FAISS execution path
        store = get_faiss_vectorstore()
        predicate = build_faiss_filter_callable(filters)
        docs_and_scores = await store.asimilarity_search_with_relevance_scores(
            query=query_text,
            k=top_k,
            filter=predicate,
            fetch_k=top_k * 10,  # Over-fetch before applying callable filter
        )

    cards: List[ProductCardResponse] = []
    for doc, score in docs_and_scores:
        m = doc.metadata
        reviews_raw = m.get("past_user_reviews_json", "[]")
        reviews_list = json.loads(reviews_raw) if isinstance(reviews_raw, str) else reviews_raw
        sizes_raw = m.get("available_sizes", "")
        sizes_list = sizes_raw.split("|") if isinstance(sizes_raw, str) else sizes_raw

        cards.append(ProductCardResponse(
            product_id=m["id"],
            sku=m["sku"],
            brand=m["brand"],
            department=m["department"],
            category=m["category"],
            sub_type=m["sub_type"],
            product_title=m["title"],
            material_type=m["material_type"],
            collar_or_waist_type=m["collar_or_waist_type"],
            color=m["color"],
            pattern=m["pattern"],
            fit_type=m["fit_type"],
            available_sizes=sizes_list,
            mrp_inr=int(m["mrp_inr"]),
            discount_pct=int(m["discount_pct"]),
            selling_price_inr=int(m["selling_price_inr"]),
            overall_rating=float(m["overall_rating"]),
            rating_count=int(m["rating_count"]),
            past_user_ratings_breakdown=m["past_user_ratings_breakdown"],
            past_user_reviews=[UserReviewItem(**r) for r in reviews_list],
            care_instructions=m["care_instructions"],
            relevance_score=round(float(score), 4),
        ))
    return cards
```

### 4.5 LangGraph Stateful Workflow with `nvidia/nemotron-3.5-super-vl:free` (`backend/app/rag/graph.py`)

```python
import json
import re
from typing import Annotated, List, Optional, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from app.core.config import settings
from app.rag.openrouter import chat_llm, parser_llm
from app.rag.retriever import execute_vector_search
from app.schemas.chat import CatalogFilterSchema, ProductCardResponse

class FashionRAGState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_query: str
    image_url: Optional[str]
    semantic_search_query: str
    intent: str
    active_filters: CatalogFilterSchema
    candidate_products: List[ProductCardResponse]
    reranked_products: List[ProductCardResponse]
    filter_relaxed: bool
    final_answer: str

async def parse_query_and_filters_node(state: FashionRAGState) -> dict:
    """
    Uses nvidia/nemotron-3.5-super-vl:free to parse text + optional outfit photo
    into strict metadata filters and a semantic search query.
    """
    system_prompt = (
        "You are an expert Fashion E-Commerce Query Analyzer. "
        "Return ONLY valid JSON with keys: "
        '{"intent": "product_discovery|styling_advice", '
        '"department": "Men|Women|Kids|Accessories|null", '
        '"category": "T-Shirt|Shirt|Short|Pant|Bags & Backpacks|Watches & Jewelry|Belts, Eyewear & Small Accessories|null", '
        '"material_type": "string or null", '
        '"collar_or_waist_type": "string or null", '
        '"color": "string or null", '
        '"max_price_inr": integer or null, '
        '"min_rating": float or null, '
        '"semantic_query": "dense search keywords describing the garment, fabric, collar, and fit"}'
    )

    # Support multimodal visual search if the user provided an image_url
    if state.get("image_url"):
        user_content = [
            {"type": "text", "text": f"User query: {state['user_query']}"},
            {"type": "image_url", "image_url": {"url": state["image_url"]}},
        ]
    else:
        user_content = state["user_query"]

    resp = await parser_llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ])

    raw_text = resp.content if isinstance(resp.content, str) else str(resp.content)
    json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    parsed_dict = json.loads(json_match.group(0)) if json_match else {}

    explicit = state.get("active_filters") or CatalogFilterSchema()
    merged_filters = CatalogFilterSchema(
        department=explicit.department or parsed_dict.get("department"),
        category=explicit.category or parsed_dict.get("category"),
        material_type=explicit.material_type or parsed_dict.get("material_type"),
        collar_or_waist_type=explicit.collar_or_waist_type or parsed_dict.get("collar_or_waist_type"),
        color=explicit.color or parsed_dict.get("color"),
        max_price_inr=explicit.max_price_inr or parsed_dict.get("max_price_inr"),
        min_rating=explicit.min_rating or parsed_dict.get("min_rating"),
    )

    return {
        "intent": parsed_dict.get("intent", "product_discovery"),
        "semantic_search_query": parsed_dict.get("semantic_query") or state["user_query"],
        "active_filters": merged_filters,
    }

async def retrieve_node(state: FashionRAGState) -> dict:
    """Queries ChromaDB or FAISS using nvidia/nemotron-3-embed-1b:free embeddings."""
    candidates = await execute_vector_search(
        query_text=state["semantic_search_query"],
        filters=state["active_filters"],
        top_k=settings.TOP_K_RETRIEVAL,
    )
    return {"candidate_products": candidates}

async def grade_and_rerank_node(state: FashionRAGState) -> dict:
    """
    Reranks candidates by combining vector similarity score, overall_rating weight,
    and keyword overlap in past buyer reviews.
    """
    query_terms = set(state["user_query"].lower().split())
    scored = []
    for item in state["candidate_products"]:
        review_blob = " ".join(r.review.lower() for r in item.past_user_reviews)
        review_bonus = sum(0.03 for t in query_terms if len(t) > 3 and t in review_blob)
        rating_bonus = (item.overall_rating - 3.5) * 0.05
        composite = item.relevance_score + review_bonus + rating_bonus
        scored.append((composite, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_n = [item for _, item in scored[: settings.TOP_N_RERANK]]
    return {"reranked_products": top_n}

async def relax_filters_node(state: FashionRAGState) -> dict:
    """Relaxes secondary constraints if strict filters return fewer than 2 products."""
    f = state["active_filters"].model_copy()
    f.collar_or_waist_type = None
    f.material_type = None
    if f.max_price_inr:
        f.max_price_inr = int(f.max_price_inr * 1.2)
    return {"active_filters": f, "filter_relaxed": True}

async def generate_stylist_answer_node(state: FashionRAGState) -> dict:
    """Synthesizes a grounded stylist answer with nvidia/nemotron-3.5-super-vl:free."""
    products_context = "\n\n".join([
        f"- **{p.product_title}** (ID: `{p.product_id}`, SKU: `{p.sku}`)\n"
        f"  Material: {p.material_type} | Collar/Waist: {p.collar_or_waist_type} | Fit: {p.fit_type}\n"
        f"  Price: ₹{p.selling_price_inr} (MRP ₹{p.mrp_inr}, {p.discount_pct}% off) | Sizes: {', '.join(p.available_sizes)}\n"
        f"  Rating: {p.overall_rating}/5.0 ({p.rating_count} reviews; Breakdown: {p.past_user_ratings_breakdown})\n"
        f"  Verified Buyer Reviews: {p.past_user_reviews[0].rating}★ \"{p.past_user_reviews[0].review}\" | "
        f"{p.past_user_reviews[1].rating}★ \"{p.past_user_reviews[1].review}\""
        for p in state["reranked_products"]
    ])

    prompt = (
        "You are an AI Fashion Stylist & Product Advisor powered by NVIDIA Nemotron. "
        "Recommend the best matching products strictly from the retrieved catalog context below. "
        "Highlight fabric/material quality, collar/waist design, fit, pricing, and summarize "
        "what past buyers said in their reviews.\n\n"
        f"Retrieved Products:\n{products_context}"
    )
    response = await chat_llm.ainvoke([
        SystemMessage(content=prompt),
        HumanMessage(content=state["user_query"]),
    ])
    return {"final_answer": response.content}

def should_relax_filters(state: FashionRAGState) -> str:
    if len(state["reranked_products"]) < 2 and not state.get("filter_relaxed", False):
        return "relax_filters"
    return "generate_answer"

workflow = StateGraph(FashionRAGState)
workflow.add_node("parse_query", parse_query_and_filters_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("grade_and_rerank", grade_and_rerank_node)
workflow.add_node("relax_filters", relax_filters_node)
workflow.add_node("generate_answer", generate_stylist_answer_node)

workflow.add_edge(START, "parse_query")
workflow.add_edge("parse_query", "retrieve")
workflow.add_edge("retrieve", "grade_and_rerank")
workflow.add_conditional_edges(
    "grade_and_rerank",
    should_relax_filters,
    {"relax_filters": "relax_filters", "generate_answer": "generate_answer"},
)
workflow.add_edge("relax_filters", "retrieve")
workflow.add_edge("generate_answer", END)

fashion_rag_graph = workflow.compile()
```

### 4.6 FastAPI Streaming SSE Endpoint (`backend/app/api/v1/endpoints/chat.py`)

```python
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatQueryRequest, CatalogFilterSchema
from app.rag.graph import fashion_rag_graph

router = APIRouter(prefix="/chat", tags=["RAG Chat & Stylist"])

@router.post("/stream")
async def stream_fashion_rag_chat(payload: ChatQueryRequest):
    """Streams real-time LangGraph state updates, product cards, and Nemotron tokens via SSE."""
    async def event_generator():
        initial_state = {
            "user_query": payload.query,
            "image_url": payload.image_url,
            "active_filters": payload.explicit_filters or CatalogFilterSchema(),
            "filter_relaxed": False,
        }
        async for event in fashion_rag_graph.astream_events(initial_state, version="v2"):
            kind = event["event"]
            if kind == "on_chain_end" and event["name"] == "parse_query":
                out = event["data"].get("output", {})
                if "active_filters" in out:
                    yield f"data: {json.dumps({'type': 'filters', 'data': out['active_filters'].model_dump()})}\n\n"

            elif kind == "on_chain_end" and event["name"] == "grade_and_rerank":
                out = event["data"].get("output", {})
                products = [p.model_dump() for p in out.get("reranked_products", [])]
                yield f"data: {json.dumps({'type': 'products', 'data': products})}\n\n"

            elif kind == "on_chat_model_stream" and event.get("metadata", {}).get("langgraph_node") == "generate_answer":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

## 5. Offline Batch Ingestion Script for ChromaDB & FAISS (`backend/scripts/ingest_5lakh_catalog.py`)

```python
import argparse
import csv
import json
import os
import chromadb
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app.core.config import settings
from app.rag.openrouter import get_openrouter_embeddings

BATCH_SIZE = 500

def row_to_document(row: dict) -> Document:
    reviews = [
        {"rating": int(row["latest_user_review_rating"]), "review": row["latest_user_review_text"], "verified_buyer": True},
        {"rating": int(row["second_user_review_rating"]), "review": row["second_user_review_text"], "verified_buyer": True},
    ]
    # ChromaDB requires flat primitive metadata values (str, int, float, bool)
    metadata = {
        "id": row["product_id"],
        "sku": row["sku"],
        "brand": row["brand"],
        "department": row["department"],
        "category": row["category"],
        "sub_type": row["sub_type"],
        "title": row["product_title"],
        "material_type": row["material_type"],
        "collar_or_waist_type": row["collar_or_waist_type"],
        "color": row["color"],
        "pattern": row["pattern"],
        "fit_type": row["fit_type"],
        "available_sizes": row["available_sizes"],
        "mrp_inr": int(row["mrp_inr"]),
        "discount_pct": int(row["discount_pct"]),
        "selling_price_inr": int(row["selling_price_inr"]),
        "overall_rating": float(row["overall_rating"]),
        "rating_count": int(row["rating_count"]),
        "past_user_ratings_breakdown": row["past_user_ratings_breakdown"],
        "past_user_reviews_json": json.dumps(reviews, ensure_ascii=False),
        "care_instructions": row["care_instructions"],
    }
    return Document(page_content=row["rag_search_summary"], metadata=metadata)

def ingest_catalog(csv_path: str, store_type: str, max_rows: int = 500000):
    embeddings = get_openrouter_embeddings()

    if store_type == "chromadb":
        client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        vectorstore = Chroma(
            client=client,
            collection_name=settings.CHROMA_PRODUCT_COLLECTION,
            embedding_function=embeddings,
        )
    else:
        os.makedirs(settings.FAISS_INDEX_DIR, exist_ok=True)
        vectorstore = None

    batch_docs, batch_ids = [], []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            if idx > max_rows:
                break
            batch_docs.append(row_to_document(row))
            batch_ids.append(row["product_id"])

            if len(batch_docs) >= BATCH_SIZE:
                if store_type == "chromadb":
                    vectorstore.add_documents(documents=batch_docs, ids=batch_ids)
                else:
                    if vectorstore is None:
                        vectorstore = FAISS.from_documents(batch_docs, embeddings)
                    else:
                        vectorstore.add_documents(batch_docs)
                print(f"[{store_type.upper()}] Indexed {idx:,} / {max_rows:,} products using {settings.EMBEDDING_MODEL}...")
                batch_docs.clear()
                batch_ids.clear()

    if batch_docs:
        if store_type == "chromadb":
            vectorstore.add_documents(documents=batch_docs, ids=batch_ids)
        else:
            if vectorstore is None:
                vectorstore = FAISS.from_documents(batch_docs, embeddings)
            else:
                vectorstore.add_documents(batch_docs)

    if store_type == "faiss" and vectorstore is not None:
        vectorstore.save_local(settings.FAISS_INDEX_DIR)
        print(f"Saved FAISS index to {settings.FAISS_INDEX_DIR}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="../../data/fashion_catalog_5lakh.csv")
    parser.add_argument("--store", choices=["chromadb", "faiss"], default="chromadb")
    parser.add_argument("--limit", type=int, default=500000)
    args = parser.parse_args()
    ingest_catalog(args.csv, args.store, args.limit)
```

## 6. React Frontend Integration (`frontend/src/hooks/useRagStream.ts`)

```typescript
import { useState, useCallback } from "react";

export interface UserReview {
  rating: number;
  review: string;
  verified_buyer: boolean;
}

export interface ProductCard {
  product_id: string;
  sku: string;
  brand: string;
  department: string;
  category: string;
  sub_type: string;
  product_title: string;
  material_type: string;
  collar_or_waist_type: string;
  color: string;
  fit_type: string;
  available_sizes: string[];
  mrp_inr: number;
  discount_pct: number;
  selling_price_inr: number;
  overall_rating: number;
  rating_count: number;
  past_user_ratings_breakdown: string;
  past_user_reviews: UserReview[];
}

export function useRagStream() {
  const [streamedAnswer, setStreamedAnswer] = useState<string>("");
  const [products, setProducts] = useState<ProductCard[]>([]);
  const [inferredFilters, setInferredFilters] = useState<Record<string, unknown>>({});
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const sendQuery = useCallback(
    async (sessionId: string, query: string, explicitFilters = {}, imageUrl?: string) => {
      setIsLoading(true);
      setStreamedAnswer("");
      setProducts([]);

      const response = await fetch("/api/v1/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          query,
          image_url: imageUrl || null,
          explicit_filters: explicitFilters,
        }),
      });

      if (!response.body) {
        setIsLoading(false);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.replace("data: ", "").trim();
          if (payload === "[DONE]") {
            setIsLoading(false);
            return;
          }
          try {
            const parsed = JSON.parse(payload);
            if (parsed.type === "filters") {
              setInferredFilters(parsed.data);
            } else if (parsed.type === "products") {
              setProducts(parsed.data);
            } else if (parsed.type === "token") {
              setStreamedAnswer((prev) => prev + parsed.content);
            }
          } catch {
            // Ignore partial JSON chunks across stream boundaries
          }
        }
      }
      setIsLoading(false);
    },
    []
  );

  return { streamedAnswer, products, inferredFilters, isLoading, sendQuery };
}
```

## 7. Production Deployment (`docker-compose.yml` with ChromaDB & FAISS Volume)

```yaml
version: "3.9"

services:
  chromadb:
    image: chromadb/chroma:0.5.20
    ports:
      - "8001:8000"
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
    volumes:
      - chroma_data:/chroma/chroma
    restart: always

  redis:
    image: redis/redis-stack-server:7.2.0-v10
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: always

  backend:
    build:
      context: ./backend
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./data/vector_indices:/app/data/vector_indices
    depends_on:
      - chromadb
      - redis
    command: >
      gunicorn app.main:app
      --workers 4
      --worker-class uvicorn.workers.UvicornWorker
      --bind 0.0.0.0:8000
      --timeout 120

  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  chroma_data:
  redis_data:
```