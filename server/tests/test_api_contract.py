import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_all_success_responses_are_typed_for_vehicle_client(tmp_path):
    app = create_app(Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode="mock"))
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
        expected = {
            ("/api/v1/health", "get"): "HealthResponse",
            ("/api/v1/feed", "get"): "FeedResponse",
            ("/api/v1/contents/{content_id}", "get"): "ContentDetail",
            ("/api/v1/contents/{content_id}/explain", "post"): "ExplainResponse",
        }
        for (path, method), name in expected.items():
            response = schema["paths"][path][method]["responses"]["200"]
            assert response["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/" + name
        assert schema["components"]["schemas"]["FeedResponse"]["properties"]["top3"]["maxItems"] == 3
        detail = client.get("/api/v1/contents/mock:news-science").json()
        assert {"id", "is_expired", "tts_eligible", "rights_status", "data_mode"} <= detail.keys()
        assert detail["tts_eligible"] is True and detail["data_mode"] == "MOCK"


def test_exported_openapi_matches_vehicle_contract(tmp_path):
    app = create_app(
        Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode="mock"), seed_demo=False
    )
    exported = json.loads(
        (Path(__file__).resolve().parents[2] / "docs/openapi.json").read_text(encoding="utf-8")
    )
    current = app.openapi()
    assert exported["paths"] == current["paths"], "Run python scripts/export_openapi.py"
    assert exported["components"] == current["components"], "Run python scripts/export_openapi.py"
