from __future__ import annotations

from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field

Department = Literal["Men", "Women", "Kids", "Accessories"]
Category = Literal[
    "T-Shirt",
    "Shirt",
    "Short",
    "Pant",
    "Bags & Backpacks",
    "Watches & Jewelry",
    "Belts, Eyewear & Small Accessories",
]


class UserReviewItem(BaseModel):
    rating: int = Field(ge=1, le=5)
    review: str
    verified_buyer: bool = False


class CatalogFilterSchema(BaseModel):
    department: Department | None = None
    category: Category | None = None
    material_type: str | None = None
    collar_or_waist_type: str | None = None
    color: str | None = None
    fit_type: str | None = None
    max_price_inr: int | None = Field(default=None, ge=0, le=500_000)
    min_rating: float | None = Field(default=None, ge=1.0, le=5.0)


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
    available_sizes: list[str]
    mrp_inr: int
    discount_pct: int
    selling_price_inr: int
    overall_rating: float
    rating_count: int
    past_user_ratings_breakdown: str
    past_user_reviews: list[UserReviewItem]
    care_instructions: str
    relevance_score: float = 0.0


class ChatQueryRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    query: str = Field(min_length=2, max_length=1000)
    image_url: AnyHttpUrl | None = None
    explicit_filters: CatalogFilterSchema | None = None


class ChatQueryResponse(BaseModel):
    session_id: str
    answer: str
    inferred_filters: CatalogFilterSchema
    products: list[ProductCardResponse]
    filter_relaxed: bool = False
