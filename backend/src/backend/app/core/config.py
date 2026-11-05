from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[5]
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseModel):
    project_name: str = "Fashion E-Commerce RAG API"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    catalog_path: Path = PROJECT_ROOT / "data" / "fashion_catalog_5lakh.csv"
    vector_store_type: Literal["chromadb", "faiss", "local"] = "local"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    embedding_model: str = "nvidia/nemotron-3-embed-1b:free"
    llm_model: str = "nvidia/nemotron-3.5-super-vl:free"
    top_k_retrieval: int = Field(default=25, ge=1, le=100)
    top_n_rerank: int = Field(default=6, ge=1, le=25)

    @classmethod
    def from_environment(cls) -> "Settings":
        values: dict[str, object] = {}
        mapping = {
            "environment": "ENVIRONMENT",
            "openrouter_base_url": "OPENROUTER_BASE_URL",
            "openrouter_api_key": "OPENROUTER_API_KEY",
            "embedding_model": "EMBEDDING_MODEL",
            "llm_model": "LLM_MODEL",
            "vector_store_type": "VECTOR_STORE_TYPE",
            "catalog_path": "CATALOG_PATH",
        }
        for field_name, environment_name in mapping.items():
            value = os.getenv(environment_name)
            if value:
                if field_name == "catalog_path":
                    catalog_path = Path(value)
                    value = catalog_path if catalog_path.is_absolute() else PROJECT_ROOT / catalog_path
                values[field_name] = value
        for field_name, environment_name in (
            ("top_k_retrieval", "TOP_K_RETRIEVAL"),
            ("top_n_rerank", "TOP_N_RERANK"),
        ):
            value = os.getenv(environment_name)
            if value:
                values[field_name] = int(value)
        return cls(**values)


settings = Settings.from_environment()
