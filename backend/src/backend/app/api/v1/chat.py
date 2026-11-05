from fastapi import APIRouter, HTTPException, Request

from backend.app.schemas.chat import ChatQueryRequest, ChatQueryResponse

router = APIRouter(prefix="/chat", tags=["RAG Chat"])


@router.post("/query", response_model=ChatQueryResponse)
def query_catalog(payload: ChatQueryRequest, request: Request) -> ChatQueryResponse:
    filters = payload.explicit_filters or request.app.state.default_filters()
    products = request.app.state.retriever.search(
        payload.query,
        filters,
        request.app.state.settings.top_n_rerank,
    )
    relaxed = False
    if len(products) < 2:
        relaxed_filters = filters.model_copy(
            update={"material_type": None, "collar_or_waist_type": None}
        )
        products = request.app.state.retriever.search(
            payload.query,
            relaxed_filters,
            request.app.state.settings.top_n_rerank,
        )
        relaxed = relaxed_filters != filters
    answer = (
        f"Found {len(products)} matching products."
        if products
        else "We couldn't find an exact match. Try broadening your filters."
    )
    return ChatQueryResponse(
        session_id=payload.session_id,
        answer=answer,
        inferred_filters=filters,
        products=products,
        filter_relaxed=relaxed,
    )


@router.get("/products/{product_id}")
def get_product(product_id: str, request: Request):
    product = request.app.state.retriever.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
