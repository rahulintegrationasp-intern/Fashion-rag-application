import type { CatalogFilters, SearchResponse } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function searchCatalog(
  query: string,
  filters: CatalogFilters,
): Promise<SearchResponse> {
  const response = await fetch(`${API_URL}/api/v1/chat/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: crypto.randomUUID(),
      query,
      explicit_filters: Object.keys(filters).length ? filters : null,
    }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "The catalog service could not complete your search.");
  }
  return response.json() as Promise<SearchResponse>;
}
