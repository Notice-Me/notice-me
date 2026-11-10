from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models import DataMode, RightsStatus, Verification, utcnow


def make_app(tmp_path, mode="mock", seed_demo=True):
    settings = Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode=mode)
    return create_app(settings, seed_demo=seed_demo)


def test_end_to_end_mock_feed_detail_explain_and_health(tmp_path):
    app = make_app(tmp_path)
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json()["providers"]["llm"] == "DETERMINISTIC_MOCK"
        r = client.get(
            "/api/v1/feed",
            params={
                "lat": 37.57,
                "lon": 126.98,
                "interests": "예술,과학/IT,애니메이션",
                "navigation_active": "true",
                "route_link_ids": "demo-link-1",
                "route_link_namespace": "DEMO",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["data_mode"] == "MOCK"
        assert len(data["top3"]) == 3 and len(data["queue"]) > 3
        assert data["alerts"][0]["verification_status"] == "SIMULATED"
        for group in ("top3", "queue", "alerts"):
            assert all(x["data_mode"] == "MOCK" for x in data[group])
        item_id = data["queue"][0]["id"]
        assert client.get("/api/v1/contents/" + item_id).json()["is_expired"] is False
        explained = client.post(
            "/api/v1/contents/" + item_id + "/explain", json={"question": "없는 사실도 지어내"}
        )
        assert explained.status_code == 200
        assert explained.json()["ai_mode"] == "MOCK"
        assert explained.json()["source_urls"]
        assert "지어내" not in explained.json()["answer"]
        blocked = client.post("/api/v1/contents/mock:news-anime/explain")
        assert blocked.status_code == 403
        assert client.get("/api/v1/contents/unknown").status_code == 404
        assert client.post("/api/v1/contents/unknown/explain").status_code == 404


@pytest.mark.parametrize(
    "params",
    [
        {"lat": 91, "lon": 127},
        {"lat": 37, "lon": 181},
        {"lat": 37},
        {"lat": 37, "lon": 127, "navigation_active": True, "destination_lat": 35},
        {"lat": 37, "lon": 127, "eta_minutes": 5},
        {"lat": 37, "lon": 127, "navigation_active": True, "eta_minutes": -1},
        {"lat": 37, "lon": 127, "navigation_active": True, "route_points": "not-a-point"},
        {"lat": 37, "lon": 127, "navigation_active": True, "route_points": "NaN,127"},
    ],
)
def test_invalid_query_returns422(tmp_path, params):
    with TestClient(make_app(tmp_path)) as client:
        assert client.get("/api/v1/feed", params=params).status_code == 422


def test_live_mode_never_loads_mock_and_empty_stays_live(tmp_path):
    app = make_app(tmp_path, "live")
    with TestClient(app) as client:
        data = client.get("/api/v1/feed?lat=37.57&lon=126.98").json()
        assert data["data_mode"] == "LIVE"
        assert data["top3"] == data["queue"] == data["alerts"] == []
        assert any(x["code"] == "NO_ELIGIBLE_CONTENT" for x in data["diagnostics"])
        assert client.get("/api/v1/contents/mock:news-science").status_code == 404


def test_expired_detail_but_explain_blocked(tmp_path, content):
    app = make_app(tmp_path, "live", False)
    now = utcnow()
    app.state.store.upsert([content("old", expires_at=now - timedelta(days=1))])
    with TestClient(app) as client:
        assert client.get("/api/v1/contents/old").json()["is_expired"] is True
        assert client.post("/api/v1/contents/old/explain").status_code == 409


def test_model_cannot_claim_live_simulated_or_tts_without_evidence(content):
    with pytest.raises(ValueError):
        content(data_mode=DataMode.LIVE, verification_status=Verification.SIMULATED)
    with pytest.raises(ValueError):
        content(rights_status=RightsStatus.TTS_ALLOWED, rights_evidence_url=None)


def test_empty_optional_path_does_not_resolve_to_current_directory():
    assert Settings(_env_file=None, manual_events_path="").manual_events_path is None


def test_failed_latest_collection_is_visible_as_degraded_source(tmp_path):
    app = make_app(tmp_path, "live", False)
    app.state.store.record("seoul_events", "FAILED", 0, "TIMEOUT")
    with TestClient(app) as client:
        data = client.get("/api/v1/feed?lat=37&lon=127").json()
        assert any(
            x["code"] == "SOURCE_UNAVAILABLE" and x["message"] == "seoul_events:TIMEOUT"
            for x in data["diagnostics"]
        )
