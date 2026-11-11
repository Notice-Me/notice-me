import json
from types import SimpleNamespace

import pytest

from app import cli
from app.config import Settings
from app.storage import Store


@pytest.mark.parametrize("selected", [["seoul_city"], ["seoul_events", "seoul_incidents"]])
async def test_public_selection_never_calls_unselected_sources(tmp_path, monkeypatch, selected):
    calls = []

    def make_provider(name):
        class FakeProvider:
            def __init__(self, *args):
                self.name = name
                self.http = SimpleNamespace(last_http_status=200)

            async def collect(self, now):
                calls.append(self.name)
                assert self.name in selected
                return [], {"test_only": True}

        return FakeProvider

    for attribute, name in [
        ("SeoulEvents", "seoul_events"),
        ("SeoulCity", "seoul_city"),
        ("SeoulIncidents", "seoul_incidents"),
        ("TourEvents", "tourapi"),
    ]:
        monkeypatch.setattr(cli, attribute, make_provider(name))
    settings = Settings(_env_file=None, db_path=tmp_path / "test.db", manual_events_path=tmp_path / "missing")
    store = Store(settings.db_path)
    reports = await cli.collect_public(settings, store, selected=selected)
    assert calls == selected and [x["provider"] for x in reports] == selected


async def test_ingest_selected_weather_does_not_search_news(tmp_path, monkeypatch, capsys):
    settings = Settings(_env_file=None, db_path=tmp_path / "test.db")
    monkeypatch.setattr(cli, "Settings", lambda: settings)

    async def collect(settings, store, selected):
        assert selected == ["seoul_city"]
        return [{"provider": "seoul_city", "status": "SUCCESS"}]

    async def no_news(*args, **kwargs):
        pytest.fail("Weather handoff must not consume news quota")

    monkeypatch.setattr(cli, "collect_public", collect)
    monkeypatch.setattr(cli, "collect_news", no_news)
    args = SimpleNamespace(
        command="ingest",
        public_provider=["seoul_city"],
        keyword=None,
        provider=None,
        window_hours=None,
        max_requests=None,
        report=tmp_path / "report.json",
    )
    await cli.run(args)
    report = json.loads(args.report.read_text(encoding="utf-8"))
    assert report["results"][0]["provider"] == "seoul_city"
    assert "news" not in report and report["news_request_budget"]["used"] == 0
