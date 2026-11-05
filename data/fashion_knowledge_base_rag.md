# Fashion E-Commerce Domain Knowledge Base (RAG Reference Document)

## 1. Catalog Taxonomy & Department Overview
This knowledge base pairs with `fashion_catalog_5lakh.csv` (500,000 structured SKU records) and `fashion_rag_chunks_10k.jsonl` (10,000 pre-chunked vector documents) to power hybrid Retrieval-Augmented Generation (RAG) for a full-stack fashion e-commerce platform covering **Men, Women, Kids, and Accessories**.

| Department | Core Categories | Material Highlights | Collar / Waist Constructions | Price Range (INR) |
| :--- | :--- | :--- | :--- | :--- |
| **Men** | T-Shirt, Shirt, Short, Pant | Supima Cotton, 100% European Linen, 13oz Raw Selvedge Denim, Merino Wool-Polyester Blend | Crew Neck, Polo Collar, Spread Collar, Cuban Camp Collar, Mandarin Band Collar, Flat-Front & Pleated Waists | ₹399 – ₹7,999 |
| **Women** | T-Shirt, Shirt, Short, Pant | Mulberry Silk Crepe, Tencel Modal-Spandex, Pure Flax Linen, Ponte Roma Knit, Vintage Rigid Denim | Scoop Neck, Boat Neck, Peter Pan Collar, Tie-Neck Bow Collar, Johnny Collar, High-Rise Paperbag Waist | ₹349 – ₹6,999 |
| **Kids** | T-Shirt, Shirt, Short, Pant | 100% GOTS Organic Cotton, Hypoallergenic Combed Cotton, Loopback French Terry, Fine-Wale Corduroy | Tagless Ribbed Crew Neck, Snap-Button Shoulder Neck, Internal Button-Adjustable Elastic Waist | ₹249 – ₹2,299 |
| **Accessories** | Bags & Backpacks, Watches & Jewelry, Belts, Eyewear & Small Accessories | Full-Grain Vegetable-Tanned Leather, 316L Surgical Stainless Steel, 925 Sterling Silver, 6A Mulberry Silk | Butterfly Deployment Clasp, Brushed Nickel Pin Buckle, Adjustable Padded Shoulder Straps | ₹499 – ₹49,999 |

## 2. Fabric & Material Guide for AI Shopping Assistant
- **100% Combed & Supima Cotton**: Extra-long staple fibers brushed to remove short strands; highly breathable, pill-resistant, and ideal for everyday crew-neck and polo t-shirts.
- **100% European Linen & Flax Blends**: Naturally thermoregulating with high moisture-wicking properties; best recommended for humid summer weather, resort wear, and casual shirts/shorts.
- **13oz Selvedge & Stretch Denim**: Heavyweight twill weave; raw selvedge molds to the wearer over time, while 2–3% elastane blends offer immediate mobility for slim and bootcut fits.
- **Tencel Modal & Lyocell**: Sustainably regenerated cellulose fiber with a silky drape and cool touch; frequently used in women's tops, palazzos, and culottes.
- **100% GOTS Organic Cotton (Kids)**: Certified free from harsh chemical dyes and formaldehyde finishes; paired with tagless necklines for sensitive skin.
- **Full-Grain Leather & 316L Stainless Steel (Accessories)**: Top-tier durability for messenger bags, reversible dress belts, and sapphire-crystal chronographs.

## 3. Collar & Neckline Styling Recommendations
- **Spread & Cutaway Collars**: Best paired with formal trousers, blazers, and wider tie knots for corporate or wedding occasions.
- **Button-Down & Oxford Collars**: Smart-casual staple that stays neat without a tie; pairs effortlessly with chinos or dark denim.
- **Cuban Camp & Mandarin Collars**: Relaxed, open-neck or band-collar silhouettes tailored for warm-weather vacations and festive evenings.
- **Peter Pan, Tie-Neck & Scoop Necks**: Feminine silhouettes offering balanced framing for workwear blouses and layered outfits.

## 4. Past User Ratings & Review Interpretation Rules for RAG
Every product record contains:
- `overall_rating` (3.2 to 4.9 scale) and `rating_count` (12 to 4,850 verified reviews).
- `past_user_ratings_breakdown`: Exact 5-star to 1-star distribution (e.g., `5★:62%|4★:23%|3★:9%|2★:4%|1★:2%`).
- `latest_user_review_text` and `second_user_review_text`: Grounded buyer feedback highlighting sizing accuracy, shrinkage resistance, stitching durability, and color fastness.
