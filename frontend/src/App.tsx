import { FormEvent, useState } from "react";
import { searchCatalog } from "./api";
import type { CatalogFilters, Product, SearchResponse } from "./types";

const categories = ["All categories", "T-Shirt", "Shirt", "Short", "Pant", "Bags & Backpacks"];
const departments = ["All departments", "Men", "Women", "Kids", "Accessories"];

function ProductCard({ product }: { product: Product }) {
  return (
    <article className="product-card">
      <div className="product-art" aria-hidden="true">
        <span>{product.category}</span>
        <strong>{product.color.slice(0, 1)}</strong>
      </div>
      <div className="product-info">
        <div className="card-topline">
          <span className="eyebrow">{product.brand}</span>
          <span className="rating">★ {product.overall_rating.toFixed(1)}</span>
        </div>
        <h3>{product.product_title}</h3>
        <p className="muted">{product.material_type} · {product.fit_type}</p>
        <div className="price-row">
          <strong>₹{product.selling_price_inr.toLocaleString("en-IN")}</strong>
          <del>₹{product.mrp_inr.toLocaleString("en-IN")}</del>
          <span className="discount">{product.discount_pct}% off</span>
        </div>
        <div className="size-row">
          {product.available_sizes.slice(0, 5).map((size) => <span key={size}>{size}</span>)}
        </div>
      </div>
    </article>
  );
}

export default function App() {
  const [query, setQuery] = useState("breathable linen shirts for everyday style");
  const [filters, setFilters] = useState<CatalogFilters>({});
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event?: FormEvent, nextQuery = query) {
    event?.preventDefault();
    if (nextQuery.trim().length < 2) return;
    setLoading(true);
    setError("");
    try {
      setResult(await searchCatalog(nextQuery.trim(), filters));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function updateFilter(key: keyof CatalogFilters, value: string) {
    setFilters((current) => ({
      ...current,
      [key]: value && !value.startsWith("All ") ? value : undefined,
    }));
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="logo" href="/">THREAD<span>LINE</span></a>
        <nav><a href="#discover">Discover</a><a href="#how-it-works">How it works</a></nav>
        <div className="status-pill"><i /> Catalog online</div>
      </header>

      <main>
        <section className="hero" id="discover">
          <div className="hero-copy">
            <p className="kicker">AI-POWERED STYLE SEARCH</p>
            <h1>Find the pieces<br /><em>worth wearing.</em></h1>
            <p className="hero-text">Describe what you want in your own words. Threadline searches the catalog for the right material, fit, color, and value.</p>
            <form className="search-box" onSubmit={submit}>
              <span className="search-icon">⌕</span>
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try “summer shirt under ₹2,500”" />
              <button type="submit" disabled={loading}>{loading ? "Searching…" : "Search"} <span>↗</span></button>
            </form>
            <div className="suggestions">
              <span>Try</span>
              {["minimal black shirt", "kids party wear", "linen under ₹2000"].map((item) => (
                <button key={item} onClick={() => { setQuery(item); void submit(undefined, item); }}>{item}</button>
              ))}
            </div>
          </div>
          <div className="hero-art" aria-label="Fashion editorial illustration">
            <div className="sun-disc" /><div className="art-label">CURATED<br />FOR YOU</div>
            <div className="silhouette silhouette-one" /><div className="silhouette silhouette-two" />
          </div>
        </section>

        <section className="workspace">
          <aside className="filters">
            <div className="section-heading"><span>Refine your search</span><button onClick={() => setFilters({})}>Reset</button></div>
            <label>Department<select value={filters.department ?? "All departments"} onChange={(event) => updateFilter("department", event.target.value)}>{departments.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label>Category<select value={filters.category ?? "All categories"} onChange={(event) => updateFilter("category", event.target.value)}>{categories.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label>Budget <span className="label-value">{filters.max_price_inr ? `₹${filters.max_price_inr}` : "Any"}</span><input type="range" min="500" max="10000" step="500" value={filters.max_price_inr ?? 10000} onChange={(event) => setFilters({ ...filters, max_price_inr: Number(event.target.value) === 10000 ? undefined : Number(event.target.value) })} /></label>
            <label>Minimum rating<select value={filters.min_rating ?? ""} onChange={(event) => setFilters({ ...filters, min_rating: event.target.value ? Number(event.target.value) : undefined })}><option value="">Any rating</option><option value="4">4.0+ stars</option><option value="4.5">4.5+ stars</option><option value="4.8">4.8+ stars</option></select></label>
            <button className="apply-button" onClick={() => void submit()}>Apply filters</button>
          </aside>

          <section className="results">
            <div className="results-header"><div><p className="kicker">YOUR EDIT</p><h2>{result ? `${result.products.length} pieces to consider` : "A sharper way to shop"}</h2></div>{result && <span className="result-count">Sorted by relevance</span>}</div>
            {error && <div className="notice error">{error}</div>}
            {result?.filter_relaxed && <div className="notice">We broadened the secondary filters to find more options for you.</div>}
            {result && <p className="answer">{result.answer}</p>}
            {!result && !loading && <div className="empty-state"><div className="empty-mark">✦</div><h3>Your next favorite is one search away.</h3><p>Start with a mood, a material, or a budget and we’ll surface the best matches.</p></div>}
            {loading && <div className="loading-grid">{[1, 2, 3].map((item) => <div className="skeleton" key={item} />)}</div>}
            {result && !loading && <div className="product-grid">{result.products.map((product) => <ProductCard key={product.product_id} product={product} />)}</div>}
            {result && !loading && result.products.length === 0 && <div className="empty-state compact"><h3>No exact match yet.</h3><p>Try removing a filter or widening your budget.</p></div>}
          </section>
        </section>

        <section className="how-it-works" id="how-it-works"><p className="kicker">THE THREADLINE METHOD</p><h2>Less scrolling.<br /><em>More finding.</em></h2><div className="method-grid"><div><b>01</b><h3>Tell us what matters</h3><p>Search naturally by style, fabric, occasion, price, or all of it together.</p></div><div><b>02</b><h3>We read between the threads</h3><p>Semantic matching and catalog signals find options that fit the whole brief.</p></div><div><b>03</b><h3>Choose with confidence</h3><p>See ratings, materials, sizing, pricing, and real buyer context at a glance.</p></div></div></section>
      </main>
      <footer><span className="logo">THREAD<span>LINE</span></span><span>Made for better wardrobes.</span></footer>
    </div>
  );
}
