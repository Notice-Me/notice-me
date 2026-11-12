from copy import deepcopy
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models import DataMode, RightsStatus, Verification
from scripts.check_vehicle_api import CheckFailed, check_api, check_playback


def test_vehicle_check_accepts_mock_without_claiming_real_ai(tmp_path):
    app = create_app(Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode="mock"))
    with TestClient(app) as client:
        report = check_api(client, expect_mode="MOCK", demo_route=True)
    assert report["status"] == "SUCCESS"
    assert report["data_mode"] == report["ai_mode"] == "MOCK"
    assert report["route_context"] == "MANUAL_DEMO_LINK"
    assert report["alert_count"] == 1 and report["queue_count"] > 3
    assert report["verification_scope"] == "SERVER_HTTP_ONLY"
    assert not report["pleos_sdk_verified"] and not report["vehicle_tts_verified"]


def test_vehicle_check_rejects_mock_presented_as_live(tmp_path):
    app = create_app(Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode="mock"))
    with TestClient(app) as client:
        report = check_api(client, expect_mode="LIVE")
    assert report["status"] == "FAILED" and report["code"] == "DATA_MODE_MISMATCH"


def test_vehicle_check_does_not_call_empty_live_feed_a_success(tmp_path):
    app = create_app(Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode="live"))
    with TestClient(app) as client:
        report = check_api(client, expect_mode="LIVE")
    assert report["status"] == "FAILED" and report["code"] == "NO_ELIGIBLE_TTS_CONTENT"
    assert report["data_mode"] == "LIVE" and report["top3_count"] == 0


@pytest.fixture
def playback_feed(tmp_path):
    app = create_app(Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode="mock"))
    with TestClient(app) as client:
        return client.get(
            "/api/v1/feed",
            params={
                "lat": 37.57,
                "lon": 126.98,
                "interests": "science,art,anime,weather",
                "navigation_active": "true",
                "route_link_ids": "demo-link-1",
                "route_link_namespace": "DEMO",
            },
        ).json()


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ("missing_evidence", "PLAYBACK_RIGHTS_VIOLATION"),
        ("uncleared_alert", "PLAYBACK_RIGHTS_VIOLATION"),
        ("expired", "PLAYBACK_CONTAINS_EXPIRED_CONTENT"),
        ("stale_alert", "PLAYBACK_TRAFFIC_STALE_OR_UNMATCHED"),
        ("reversed_order", "PLAYBACK_ORDER_MISMATCH"),
        ("missing_alert", "PLAYBACK_ORDER_MISMATCH"),
    ],
)
def test_check_rejects_unsafe_or_incomplete_playback(playback_feed, change, code):
    feed = deepcopy(playback_feed)
    if change == "missing_evidence":
        feed["queue"][0]["rights_evidence_url"] = None
    elif change == "uncleared_alert":
        feed["alerts"][0]["rights_status"] = "LICENSE_UNVERIFIED"
    elif change == "expired":
        feed["queue"][0]["expires_at"] = "2000-01-01T00:00:00Z"
    elif change == "stale_alert":
        feed["alerts"][0]["fetched_at"] = "2000-01-01T00:00:00Z"
    elif change == "reversed_order":
        feed["playback_order"].reverse()
    elif change == "missing_alert":
        feed["playback_order"] = feed["playback_order"][1:]
    with pytest.raises(CheckFailed, match=code):
        check_playback(feed, datetime.now(UTC))


def test_check_rejects_screen_only_news_marked_playable(playback_feed):
    blocked = playback_feed["top3"][0]
    blocked.update(
        id="screen-only-news", content_type="NEWS", rights_status="LICENSE_UNVERIFIED", tts_eligible=True
    )
    with pytest.raises(CheckFailed, match="UNCLEARED_CONTENT_PLAYABLE"):
        check_playback(playback_feed, datetime.now(UTC))


def test_live_mode_checker_verifies_uncleared_news_without_mock_health(tmp_path, content):
    # Synthetic unit records exercise LIVE mode; they are not real provider evidence.
    now = datetime.now(UTC)
    app = create_app(Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode="live"))
    common = dict(
        published_at=now - timedelta(hours=1),
        fetched_at=now,
        expires_at=now + timedelta(hours=1),
        data_mode=DataMode.LIVE,
        verification_status=Verification.VERIFIED,
        provenance="SYNTHETIC_UNIT_TEST",
    )
    app.state.store.upsert(
        [
            content(
                "spoken",
                **(
                    common
                    | {
                        "content_type": "LIFE",
                        "provenance": "PUBLIC_API:seoul_citydata;SYNTHETIC_UNIT_TEST",
                        "weather": {"area_code": "POI009", "region": "광화문·덕수궁", "observed_at": now},
                    }
                ),
            ),
            content("blocked", **common, rights_status=RightsStatus.LICENSE_UNVERIFIED),
        ]
    )
    with TestClient(app) as client:
        report = check_api(client, expect_mode="LIVE")
    assert report["status"] == "SUCCESS" and report["blocked_news_checked"] == 1
    assert "uncleared_news:403" in report["checks"]
