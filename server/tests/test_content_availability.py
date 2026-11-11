from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.fixtures import demo_contents
from app.main import create_app


@pytest.mark.parametrize(
    "scenario,expected_reason",
    [
        ("fresh", None),
        ("age_exactly_10_minutes", None),
        ("stale", "TRAFFIC_STALE"),
        ("closed", "TRAFFIC_INVALID"),
        ("impact_expired", "TRAFFIC_INVALID"),
        ("occurs_in_future", "TRAFFIC_INVALID"),
        ("missing_impact", "TRAFFIC_INVALID"),
        ("future_published", "EXPIRED_OR_FUTURE"),
        ("expired", "EXPIRED_OR_FUTURE"),
    ],
)
def test_feed_detail_and_explain_agree_on_content_validity(
    tmp_path, monkeypatch, now, scenario, expected_reason
):
    monkeypatch.setattr("app.main.utcnow", lambda: now)
    app = create_app(
        Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode="mock"), seed_demo=False
    )
    item = demo_contents(now)[-1]
    if scenario == "age_exactly_10_minutes":
        item.fetched_at = now - timedelta(minutes=10)
    elif scenario == "stale":
        item.fetched_at = now - timedelta(minutes=11)
    elif scenario == "closed":
        item.traffic.status = "CLEARED"
    elif scenario == "impact_expired":
        item.traffic.valid_until = now - timedelta(seconds=1)
    elif scenario == "occurs_in_future":
        item.traffic.occurred_at = now + timedelta(minutes=1)
    elif scenario == "missing_impact":
        item.traffic = None
    elif scenario == "future_published":
        item.published_at = now + timedelta(minutes=1)
    elif scenario == "expired":
        item.expires_at = now
    app.state.store.upsert([item])
    with TestClient(app) as client:
        feed = client.get(
            "/api/v1/feed",
            params={
                "lat": 37.57,
                "lon": 126.98,
                "navigation_active": "true",
                "route_link_ids": "demo-link-1",
                "route_link_namespace": "DEMO",
            },
        ).json()
        detail = client.get("/api/v1/contents/" + item.id).json()
        explanation = client.post("/api/v1/contents/" + item.id + "/explain")
    eligible = expected_reason is None
    assert bool(feed["alerts"]) == eligible
    assert detail["tts_eligible"] == eligible
    assert explanation.status_code == (200 if eligible else 409)


def test_stale_ordinary_content_remains_readable_without_tts(tmp_path, monkeypatch, now, content):
    monkeypatch.setattr("app.main.utcnow", lambda: now)
    item = content("expired-news", expires_at=now)
    app = create_app(
        Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode="live"), seed_demo=False
    )
    app.state.store.upsert([item])
    with TestClient(app) as client:
        response = client.get("/api/v1/contents/" + item.id)
        assert response.status_code == 200
        assert response.json()["is_expired"] is True
        assert response.json()["tts_eligible"] is False
        assert client.post("/api/v1/contents/" + item.id + "/explain").status_code == 409
