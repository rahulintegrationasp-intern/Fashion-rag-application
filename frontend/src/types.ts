export type Department = "Men" | "Women" | "Kids" | "Accessories";

export interface CatalogFilters {
  department?: Department;
  category?: string;
  max_price_inr?: number;
  min_rating?: number;
}

export interface UserReview {
  rating: number;
  review: string;
  verified_buyer: boolean;
}

export interface Product {
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
  pattern: string;
  fit_type: string;
  available_sizes: string[];
  mrp_inr: number;
  discount_pct: number;
  selling_price_inr: number;
  overall_rating: number;
  rating_count: number;
  past_user_ratings_breakdown: string;
  past_user_reviews: UserReview[];
  care_instructions: string;
  relevance_score: number;
}

export interface SearchResponse {
  session_id: string;
  answer: string;
  inferred_filters: CatalogFilters;
  products: Product[];
  filter_relaxed: boolean;
}
