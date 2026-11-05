# Fashion E-Commerce Synthetic Dataset (5 Lakh / 500,000 Records) for RAG

## Contents of This Archive
1. **`fashion_catalog_5lakh.csv`** — **500,000 (5 Lakh) structured product records** across **Men, Women, Kids, and Accessories**, including `rag_search_summary` pre-formatted for embedding generation.
2. **`fashion_rag_chunks_10k.jsonl`** — **10,000 JSON Lines documents** with separated `"text"` (for vector embedding) and nested `"metadata"` (for metadata filtering in Pinecone, Qdrant, ChromaDB, Weaviate, or Milvus).
3. **`fashion_knowledge_base_rag.md`** — **Domain Knowledge Base in Markdown** covering fabric properties, collar/neckline styling rules, department size guides, and review interpretation guidelines.

## Why Both CSV + JSONL + Markdown?
For a production **RAG (Retrieval-Augmented Generation)** application:
- **JSONL / CSV (`rag_search_summary` column)** gives each product a dense natural-language paragraph combining department, category, subtype (T-Shirt, Shirt, Short, Pant, Accessories), material, collar/waist type, fit, price, discount, overall rating, 5-star breakdown, and verbatim past user reviews.
- **Structured columns / JSON metadata** allow your retriever to apply **strict metadata pre-filters** (e.g., `department == "Men"`, `category == "Shirt"`, `overall_rating >= 4.2`, `selling_price_inr <= 2000`) *before* semantic vector search.
- **Markdown (`fashion_knowledge_base_rag.md`)** answers general styling, fabric-care, and sizing questions that span across individual products.

## Schema Reference (`fashion_catalog_5lakh.csv`)
| Column | Type | Description |
| :--- | :--- | :--- |
| `product_id` | String | Unique ID (`PROD-000001` to `PROD-500000`) |
| `sku` | String | Inventory SKU (`SKU-MEN-TSH-000001`, etc.) |
| `brand` | String | Brand name (20 synthetic fashion brands) |
| `department` | String | `Men`, `Women`, `Kids`, or `Accessories` |
| `category` | String | `T-Shirt`, `Shirt`, `Short`, `Pant`, `Bags & Backpacks`, `Watches & Jewelry`, `Belts, Eyewear & Small Accessories` |
| `sub_type` | String | Specific garment/accessory style (e.g., `Oxford Button-Down Shirt`, `High-Waisted Wide-Leg Palazzo Pants`) |
| `product_title` | String | Full display name of the item |
| `material_type` | String | Fabric or hardware composition (e.g., `100% European Linen`, `Supima Cotton`) |
| `collar_or_waist_type` | String | Collar style for tops (`Crew Neck`, `Polo Collar`, `Spread Collar`, `Mandarin Band Collar`) or waist/clasp construction for bottoms/accessories |
| `color` | String | Primary colorway (20 colors) |
| `pattern` | String | Surface pattern (`Solid`, `Micro-Checkered`, `Vertical Pinstripe`, etc.) |
| `fit_type` | String | Silhouette/cut (`Slim Fit`, `Regular Fit`, `Oversized Fit`, etc.) |
| `available_sizes` | String | Pipe-delimited size run (`S|M|L|XL|XXL`, `28|30|32|34|36`, etc.) |
| `occasion` | String | Recommended occasion (`Casual Everyday`, `Office & Formal Workwear`, etc.) |
| `season` | String | Recommended season (`All-Season`, `Summer / Spring`, etc.) |
| `mrp_inr` | Integer | Maximum Retail Price in INR |
| `discount_pct` | Integer | Discount percentage (`0` to `50`) |
| `selling_price_inr` | Integer | Final selling price in INR |
| `in_stock` | String | Availability status |
| `overall_rating` | Float | Aggregate rating from `3.2` to `4.9` |
| `rating_count` | Integer | Total number of past customer ratings |
| `past_user_ratings_breakdown` | String | Star distribution (`5★:...|4★:...|3★:...|2★:...|1★:...`) |
| `latest_user_review_rating` | Integer | Star rating (`1`–`5`) of most recent buyer review |
| `latest_user_review_text` | String | Verbatim review from recent buyer |
| `second_user_review_rating` | Integer | Star rating (`1`–`5`) of second buyer review |
| `second_user_review_text` | String | Verbatim review from second buyer |
| `care_instructions` | String | Washing and maintenance instructions |
| `rag_search_summary` | String | Pre-constructed natural language chunk for direct RAG embedding |
