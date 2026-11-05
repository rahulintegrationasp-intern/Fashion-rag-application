from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from backend.app.schemas.chat import (
    CatalogFilterSchema,
    ProductCardResponse,
    UserReviewItem,
)


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


def _matches(row: dict[str, str], filters: CatalogFilterSchema) -> bool:
    for field in ("department", "category", "material_type", "collar_or_waist_type", "color", "fit_type"):
        expected = getattr(filters, field)
        if expected and expected.lower() not in row[field].lower():
            return False
    if filters.max_price_inr is not None and int(row["selling_price_inr"]) > filters.max_price_inr:
        return False
    if filters.min_rating is not None and float(row["overall_rating"]) < filters.min_rating:
        return False
    return True


def _product(row: dict[str, str], query: str) -> ProductCardResponse:
    query_tokens = _tokens(query)
    searchable = " ".join(
        row[field]
        for field in ("product_title", "material_type", "collar_or_waist_type", "rag_search_summary")
    ).lower()
    lexical_score = len(query_tokens.intersection(_tokens(searchable))) / max(len(query_tokens), 1)
    rating_score = max(float(row["overall_rating"]) - 3.0, 0.0) / 2.0
    reviews = [
        UserReviewItem(
            rating=int(row["latest_user_review_rating"]),
            review=row["latest_user_review_text"],
        ),
        UserReviewItem(
            rating=int(row["second_user_review_rating"]),
            review=row["second_user_review_text"],
        ),
    ]
    return ProductCardResponse(
        product_id=row["product_id"],
        sku=row["sku"],
        brand=row["brand"],
        department=row["department"],
        category=row["category"],
        sub_type=row["sub_type"],
        product_title=row["product_title"],
        material_type=row["material_type"],
        collar_or_waist_type=row["collar_or_waist_type"],
        color=row["color"],
        pattern=row["pattern"],
        fit_type=row["fit_type"],
        available_sizes=[size for size in row["available_sizes"].split("|") if size],
        mrp_inr=int(row["mrp_inr"]),
        discount_pct=int(row["discount_pct"]),
        selling_price_inr=int(row["selling_price_inr"]),
        overall_rating=float(row["overall_rating"]),
        rating_count=int(row["rating_count"]),
        past_user_ratings_breakdown=row["past_user_ratings_breakdown"],
        past_user_reviews=reviews,
        care_instructions=row["care_instructions"],
        relevance_score=round(lexical_score * 0.8 + rating_score * 0.2, 4),
    )


class CatalogRetriever:
    def __init__(self, catalog_path: Path) -> None:
        self.catalog_path = catalog_path

    def search(
        self,
        query: str,
        filters: CatalogFilterSchema,
        limit: int,
    ) -> list[ProductCardResponse]:
        matches: list[ProductCardResponse] = []
        with self.catalog_path.open(newline="", encoding="utf-8") as catalog:
            for row in csv.DictReader(catalog):
                if _matches(row, filters):
                    matches.append(_product(row, query))
        matches.sort(key=lambda product: product.relevance_score, reverse=True)
        return matches[:limit]

    def get(self, product_id: str) -> ProductCardResponse | None:
        with self.catalog_path.open(newline="", encoding="utf-8") as catalog:
            for row in csv.DictReader(catalog):
                if row["product_id"] == product_id:
                    return _product(row, row["rag_search_summary"])
        return None

    def exists(self) -> bool:
        return self.catalog_path.is_file()
