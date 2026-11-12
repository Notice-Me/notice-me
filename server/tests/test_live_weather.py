from datetime import timedelta

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models import DataMode, FeedContext, RightsStatus, Verification, WeatherObservation
from app.providers.seoul import SeoulCity
from app.recommendation import build_feed


@pytest.fixture
def weather(content, now):
    return content(
        "seoul-city:POI009:weather",
        content_type="LIFE",
        title="광화문·덕수궁 날씨",
        brief="서울시 관측 기준 광화문·덕수궁 기온은 10도입니다.",
        interest_tags=["날씨"],
        latitude=None,
        longitude=None,
        provenance="PUBLIC_API:seoul_citydata;KOGL_TYPE1;weather_fields_only",
        weather=WeatherObservation(area_code="POI009", region="광화문·덕수궁", observed_at=now),
        expires_at=now + timedelta(hours=1),
    )


@pytest.mark.parametrize("mode", ["live", "mixed"])
def test_live_weather_only_reaches_voice_but_news_stays_on_screen(
    tmp_path, monkeypatch, now, content, weather, mode
):
    monkeypatch.setattr("app.main.utcnow", lambda: now)
    app = create_app(Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode=mode), seed_demo=False)
    # Even an otherwise licensed LIVE article is outside this MVP voice scope.
    news = content("licensed-news")
    app.state.store.upsert([weather, news])
    with TestClient(app) as client:
        result = client.get(
            "/api/v1/feed", params={"lat": 35, "lon": 129, "interests": "weather,science"}
        ).json()
        assert {x["id"] for x in result["top3"]} == {weather.id, news.id}
        assert result["playback_order"] == [weather.id]
        detail = client.get("/api/v1/contents/" + weather.id).json()
        assert detail["tts_eligible"] is True
        assert detail["weather"]["region"] == "광화문·덕수궁"
        assert detail["latitude"] is None  # Never relabel as the Busan request's weather.
        assert client.get("/api/v1/contents/" + news.id).json()["tts_eligible"] is False
        assert "LIVE_TTS_WEATHER_ONLY" in {x["code"] for x in result["diagnostics"]}


@pytest.mark.parametrize(
    "case",
    [
        "expired",
        "future_observation",
        "old_observation",
        "future_fetch",
        "no_evidence",
        "unverified",
        "legacy_no_weather",
    ],
)
def test_unsafe_weather_never_enters_queue_or_detail_tts(tmp_path, monkeypatch, now, weather, case):
    monkeypatch.setattr("app.main.utcnow", lambda: now)
    if case == "expired":
        weather.expires_at = now
    elif case == "future_observation":
        weather.weather.observed_at = now + timedelta(seconds=1)
    elif case == "old_observation":
        weather.weather.observed_at = now - timedelta(hours=1)
    elif case == "future_fetch":
        weather.fetched_at = now + timedelta(seconds=1)
    elif case == "no_evidence":
        weather.rights_status = RightsStatus.LICENSE_UNVERIFIED
        weather.rights_evidence_url = None
    elif case == "unverified":
        weather.verification_status = Verification.UNVERIFIED
    else:
        weather.weather = None
    app = create_app(
        Settings(_env_file=None, db_path=tmp_path / "test.db", data_mode="live"), seed_demo=False
    )
    app.state.store.upsert([weather])
    with TestClient(app) as client:
        result = client.get(
            "/api/v1/feed", params={"lat": 37.57, "lon": 126.98, "interests": "weather"}
        ).json()
        assert result["queue"] == result["playback_order"] == []
        assert client.get("/api/v1/contents/" + weather.id).json()["tts_eligible"] is False


def test_navigation_prioritizes_destination_without_inventing_route_or_event_time(content, now):
    current = content("current", latitude=37.57, longitude=126.98, interest_tags=[])
    destination = content("destination", latitude=35, longitude=129, interest_tags=[])
    event = content("event", content_type="EVENT", latitude=35, longitude=129)
    context = FeedContext(
        lat=37.57, lon=126.98, navigation_active=True, destination_lat=35, destination_lon=129, eta_minutes=20
    )
    result = build_feed([current, destination, event], context, now, DataMode.LIVE)
    assert [x.id for x in result.top3] == ["destination"]
    assert context.route_points == []
    assert "DRIVING_TIME_UNVERIFIED" in {x.code for x in result.diagnostics}


def test_eta_shortens_weather_queue_without_hiding_weather(weather, now):
    context = FeedContext(
        lat=37.57,
        lon=126.98,
        interests=["weather"],
        navigation_active=True,
        destination_lat=35,
        destination_lon=129,
        eta_minutes=0.25,
    )
    result = build_feed([weather], context, now, DataMode.LIVE)
    assert len(result.top3) == 1 and result.queue == []


async def test_provider_emits_named_observation_not_request_location(now):
    xml = """<SeoulRtd.citydata><RESULT><RESULT.CODE>INFO-000</RESULT.CODE></RESULT>
    <CITYDATA><AREA_NM>광화문·덕수궁</AREA_NM><WEATHER_STTS><WEATHER_STTS>
    <WEATHER_TIME>2026-11-11 09:00</WEATHER_TIME><TEMP>10.0</TEMP>
    </WEATHER_STTS></WEATHER_STTS></CITYDATA></SeoulRtd.citydata>"""
    provider = SeoulCity(transport=httpx.MockTransport(lambda _: httpx.Response(200, text=xml)))
    items, _ = await provider.collect(now)
    assert items[0].weather.observed_at == now
    assert items[0].weather.area_code == "POI009"
    assert items[0].weather.scope == "FIXED_OBSERVATION_AREA"
