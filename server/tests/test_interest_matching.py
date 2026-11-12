from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.fixtures import demo_contents
from app.interests import classify_categories, parse_interests
from app.main import create_app
from app.models import DataMode, FeedContext, RightsStatus
from app.providers.news import NewsProvider
from app.recommendation import build_feed, deduplicate
from app.routing import DemoRouting

ALIASES = ["먼작귀", "치이카와", "Chiikawa", "ちいかわ"]


def feed(items, now, interests, **context):
    return build_feed(
        items, FeedContext(lat=37.57, lon=126.98, interests=interests, **context), now, DataMode.LIVE
    )


@pytest.mark.parametrize("query", ALIASES)
@pytest.mark.parametrize("title_alias", ALIASES)
def test_multilingual_topic_matches_real_metadata_shape_without_granting_voice(
    content, now, query, title_alias
):
    item = content(
        "related",
        title=f"{title_alias} POP-UP STORE",
        interest_tags=["애니메이션"],
        rights_status=RightsStatus.LICENSE_UNVERIFIED,
    )
    result = feed([item], now, [query, "팝업스토어"])
    assert [x.id for x in result.top3] == [item.id]
    assert result.top3[0].score_reasons["interest_topic"] == 30
    assert result.top3[0].score_reasons["interest_format"] == 10
    assert result.queue == []


def test_topic_cannot_fall_back_to_generic_anime_or_nearby_news(content, now):
    items = [content("unrelated", title="다른 애니메이션 신작 발표", interest_tags=["애니메이션"])]
    assert feed(items, now, ["anime", "치이카와"]).top3 == []


@pytest.mark.parametrize("field", ["interest_tags", "source_url", "source_name", "brief"])
def test_specific_topic_requires_title_evidence_not_a_search_tag_or_url(content, now, field):
    updates = {
        field: ["치이카와"]
        if field == "interest_tags"
        else "https://example.org/chiikawa"
        if field == "source_url"
        else "치이카와"
    }
    item = content("unrelated", title="지역 예산 검토", **updates)
    assert feed([item], now, ["Chiikawa"]).top3 == []


def test_topic_and_popup_are_conjunctive_without_inventing_an_event(content, now):
    item = content("movie", title="치이카와 극장판 개봉 소식", interest_tags=["애니메이션"])
    assert feed([item], now, ["치이카와"]).top3[0].content_type == "NEWS"
    assert feed([item], now, ["치이카와", "팝업스토어"]).top3 == []


def test_formats_have_context_and_category_constraints(content, now):
    browser = content("browser", title="브라우저 팝업 차단 해제", interest_tags=["과학IT"])
    cosmetics = content("cosmetics", title="화장품 팝업스토어", interest_tags=["생활"])
    celebrity = content("celebrity", title="가수 굿즈 판매", interest_tags=["예술"])
    assert feed([browser], now, ["팝업스토어"]).top3 == []
    assert feed([cosmetics], now, ["anime", "팝업스토어"]).top3 == []
    contaminated = cosmetics.model_copy(update={"interest_tags": ["애니메이션"]})
    assert feed([contaminated], now, ["anime", "POP-UP STORE"]).top3 == []
    assert feed([celebrity], now, ["캐릭터 굿즈"]).top3 == []
    related = content("goods", title="ちいかわ グッズ 출시", interest_tags=["애니메이션"])
    assert feed([related], now, ["캐릭터 굿즈"]).top3[0].id == "goods"


def test_ascii_word_boundaries_and_search_term_do_not_manufacture_tags(now):
    assert classify_categories("A chair party is limited") == []
    assert classify_categories("IT 산업과 AI 기술") == ["과학IT"]
    provider = NewsProvider("freenews", "unused-test-key")
    result = provider.normalize(
        [
            {
                "title": "City budget review",
                "publisher": "Test",
                "original_url": "https://example.org/article",
                "published_at": now.isoformat(),
            }
        ],
        now,
        "Chiikawa",
    )
    assert result[0].interest_tags == []
    assert result[0].brief == "" and result[0].rights_status == RightsStatus.LICENSE_UNVERIFIED


def test_case_width_and_duplicate_aliases_do_not_inflate_interest_score(content, now):
    item = content("topic", title="CHIIKAWA 굿즈", interest_tags=["애니메이션"])
    one = feed([item], now, ["chiikawa"]).top3[0]
    many = feed([item], now, ["ＣＨＩＩＫＡＷＡ", *ALIASES]).top3[0]
    assert one.score == many.score
    assert many.score == round(sum(many.score_reasons.values()), 3)
    assert parse_interests(["과학/IT", "science"]).categories == {"과학IT"}


def test_unknown_keywords_are_literal_and_short_terms_do_not_bypass_filters(content, now):
    item = content("blue-lock", title="블루록 전시회", interest_tags=["애니메이션"])
    assert feed([item], now, ["블루 록"]).top3[0].id == item.id
    assert feed([item], now, [".*"]).top3 == []
    result = feed([item], now, ["x"])
    assert result.top3 == []
    assert "UNSUPPORTED_INTEREST" in {d.code for d in result.diagnostics}


def test_explicit_weather_survives_specific_topic_and_mock_baseline_stays_intact(content, now):
    weather = content(
        "weather",
        content_type="LIFE",
        title="광화문 날씨",
        interest_tags=["생활"],
        provenance="PUBLIC_API:seoul_citydata;test",
        weather={"area_code": "POI009", "region": "광화문·덕수궁", "observed_at": now},
        expires_at=now + timedelta(hours=1),
    )
    result = feed([weather], now, ["치이카와", "팝업스토어", "weather"])
    assert result.playback_order == [weather.id]
    baseline = build_feed(
        demo_contents(now),
        FeedContext(lat=37.57, lon=126.98, interests=["art", "science", "weather"]),
        now,
        DataMode.MOCK,
        DemoRouting(),
    )
    assert len(baseline.top3) == 3 and len(baseline.queue) == 5


def test_specific_event_still_requires_verified_driving_time_not_destination_eta(content, now):
    item = content(
        "event", title="치이카와 팝업스토어", content_type="EVENT", starts_at=now, venue="테스트 행사장"
    )
    result = feed(
        [item],
        now,
        ["치이카와"],
        navigation_active=True,
        destination_lat=37.57,
        destination_lon=126.98,
        eta_minutes=5,
    )
    assert result.top3 == []
    assert "DRIVING_TIME_UNVERIFIED" in {d.code for d in result.diagnostics}


def test_explicit_exhibition_type_is_evidence_and_specific_interests_do_not_hide_mock_alerts(content, now):
    item = content(
        "exhibit", title="ちいかわの世界", content_type="EXHIBITION", data_mode="MOCK", starts_at=now
    )
    context = FeedContext(
        lat=37.57,
        lon=126.98,
        interests=["치이카와", "전시회"],
        navigation_active=True,
        route_link_ids=["demo-link-1"],
        route_link_namespace="DEMO",
    )
    result = build_feed([item, demo_contents(now)[-1]], context, now, DataMode.MOCK, DemoRouting())
    assert result.top3[0].id == "exhibit"
    assert result.playback_order[0] == "mock:traffic"


def test_same_event_occurrence_deduplicates_but_other_dates_places_and_unknowns_do_not(content, now):
    original = content(
        "one", title="치이카와 팝업스토어", content_type="EVENT", starts_at=now, venue="테스트 백화점"
    )
    same = original.model_copy(update={"id": "two", "content_type": "EXHIBITION"})
    assert len(deduplicate([original, same])) == 1
    for changes in [
        {"starts_at": now + timedelta(days=1)},
        {"venue": "다른 지점"},
        {"latitude": 35.0, "longitude": 129.0},
    ]:
        assert len(deduplicate([original, original.model_copy(update={"id": "other", **changes})])) == 2
    unknown = original.model_copy(update={"venue": None, "latitude": None, "longitude": None})
    assert len(deduplicate([unknown, unknown.model_copy(update={"id": "unknown2"})])) == 2


def test_http_aliases_keep_contract_and_rights_and_do_not_store_request_history(
    tmp_path, content, now, monkeypatch
):
    monkeypatch.setattr("app.main.utcnow", lambda: now)
    app = create_app(
        Settings(_env_file=None, db_path=tmp_path / "state.db", data_mode="live"), seed_demo=False
    )
    item = content(
        "topic",
        title="ちいかわ 팝업스토어",
        interest_tags=["애니메이션"],
        rights_status=RightsStatus.LICENSE_UNVERIFIED,
    )
    app.state.store.upsert([item])
    before = app.state.store.health()
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/feed",
            params=[("lat", 37.57), ("lon", 126.98), ("interests", "먼작귀"), ("interests", "팝업스토어")],
        )
        assert response.status_code == 200
        assert response.json()["top3"][0]["id"] == item.id
        assert response.json()["queue"] == []
        assert client.get("/api/v1/contents/" + item.id).json()["tts_eligible"] is False
        assert client.post("/api/v1/contents/" + item.id + "/explain").status_code == 403
    assert app.state.store.health() == before
