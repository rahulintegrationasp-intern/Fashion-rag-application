from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app


def test_health_and_query() -> None:
    root = Path(__file__).resolve().parents[2]
    app = create_app(Settings(catalog_path=root / "data" / "fashion_catalog_5lakh.csv"))
    client = TestClient(app)

    assert client.get("/health/live").json() == {"status": "ok"}
    response = client.post(
        "/api/v1/chat/query",
        json={"session_id": "test-session", "query": "cotton shirt"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["products"]
    assert body["products"][0]["product_id"].startswith("PROD-")
