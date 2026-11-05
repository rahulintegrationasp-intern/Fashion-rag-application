from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

ModelT = TypeVar("ModelT", bound=BaseModel)


def safe_parse_llm_json(
    raw_text: str,
    schema: type[ModelT],
    default_instance: ModelT,
) -> ModelT:
    """Extract and validate an object from an unreliable model response."""
    if not raw_text:
        return default_instance
    try:
        match = re.search(r"\{.*\}", str(raw_text), re.DOTALL)
        payload: Any = json.loads(match.group(0) if match else str(raw_text))
        if not isinstance(payload, dict):
            return default_instance
        clean_payload = {
            key: value
            for key, value in payload.items()
            if value is not None and value != "null"
        }
        return schema.model_validate(clean_payload)
    except (json.JSONDecodeError, TypeError, ValidationError):
        return default_instance
