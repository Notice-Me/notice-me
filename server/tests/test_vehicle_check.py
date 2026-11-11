from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from scripts.check_vehicle_api import check_api


def test_vehicle_check_accepts_mock_without_claiming_real_ai(tmp_path):
    app = create_app(Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode="mock"))
    with TestClient(app) as client:
        report = check_api(client, expect_mode="MOCK", demo_route=True)
    assert report["status"] == "SUCCESS"
    assert report["data_mode"] == report["ai_mode"] == "MOCK"
    assert report["route_context"] == "MANUAL_DEMO_LINK"
    assert report["alert_count"] == 1 and report["queue_count"] > 3


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
