from datetime import timedelta

from app.fixtures import demo_contents
from app.models import ContentType, DataMode, FeedContext, RightsStatus, TravelAssessment, Verification
from app.recommendation import build_feed, deduplicate
from app.routing import DemoRouting


def feed(items, context, now, routing=None):
    return build_feed(items, context, now, DataMode.LIVE, routing)


def test_news_dedup_tracking_url_and_event_title(content):
    items = [
        content("a", title="과학관 로봇 전시 개최 소식이 발표됐습니다"),
        content("b", source_url="https://example.org/articles/a?utm_source=feed"),
        content("c", title="[속보] 과학관 로봇 전시 개최 소식이 발표됐습니다"),
        content("d", title="새로운 별 관측 프로젝트를 시작합니다"),
    ]
    assert len(deduplicate(items)) == 2


def test_similar_daily_story_after_24h_not_collapsed(content, now):
    a = content("a", title="오늘 정기적으로 열리는 과학관 프로그램 안내")
    b = content("b", title=a.title, published_at=now - timedelta(days=2))
    assert len(deduplicate([a, b])) == 2


def test_distinct_incidents_sharing_dataset_source_url_not_deduplicated(now):
    from app.models import Content

    original = demo_contents(now)[-1]
    first = Content.model_validate(
        {
            **original.model_dump(),
            "id": "traffic:first",
            "source_url": "https://data.seoul.go.kr/dataList/OA-13315/A/1/datasetView.do",
        }
    )
    second = Content.model_validate({**first.model_dump(), "id": "traffic:second", "title": "다른 사고"})
    assert len(deduplicate([first, second])) == 2


def test_expired_future_and_unverified_excluded(content, context, now):
    items = [
        content("expired", expires_at=now),
        content("future", published_at=now + timedelta(seconds=1)),
        content("unverified", verification_status=Verification.UNVERIFIED),
    ]
    result = feed(items, context, now)
    assert not result.top3 and not result.queue


def test_life_requires_registered_interest_and_global_interest_news(content, now):
    items = [
        content("global", latitude=-33, longitude=151),
        content("life-wrong", content_type=ContentType.LIFE, interest_tags=["육아"]),
        content("life-match", content_type=ContentType.LIFE),
    ]
    result = feed(items, FeedContext(lat=0, lon=0, interests=["과학/IT"]), now)
    assert {x.id for x in result.top3} == {"global", "life-match"}


def test_local_news_requires_location_or_interest(content, now):
    items = [content("near", interest_tags=[]), content("far", interest_tags=[], latitude=0, longitude=0)]
    result = feed(items, FeedContext(lat=37.57, lon=126.98), now)
    assert [x.id for x in result.top3] == ["near"]


def test_destination_related_news_and_score_reasons(content, now):
    item = content("destination", latitude=35, longitude=129, interest_tags=[])
    no_nav = FeedContext(lat=37.57, lon=126.98)
    nav = FeedContext(lat=37.57, lon=126.98, navigation_active=True, destination_lat=35, destination_lon=129)
    assert not feed([item], no_nav, now).top3
    result = feed([item], nav, now)
    assert result.top3[0].score_reasons["destination"] == 25
    assert result.top3[0].score == round(sum(result.top3[0].score_reasons.values()), 3)


def test_top3_max_and_unlimited_independent_voice_queue(content, context, now):
    items = [content(str(i), title=f"서로 다른 소식 {i}") for i in range(7)]
    result = feed(items, context, now)
    assert len(result.top3) == 3
    assert len(result.queue) == 7
    assert any(x.id not in {t.id for t in result.top3} for x in result.queue)


def test_rights_gate_not_satisfied_by_verified_metadata(content, context, now):
    items = [
        content("allowed"),
        content("unverified", rights_status=RightsStatus.LICENSE_UNVERIFIED, rights_evidence_url=None),
        content("link", rights_status=RightsStatus.LINK_ONLY, rights_evidence_url=None),
    ]
    result = feed(items, context, now)
    assert len(result.top3) == 3
    assert [x.id for x in result.queue] == ["allowed"]
    assert all(x.tts_eligible is False for x in result.top3 if x.id != "allowed")


def test_unknown_or_over60_driving_time_excludes_live_events(content, context, now):
    item = content(content_type=ContentType.EVENT)
    assert not feed([item], context, now).top3

    class Routing:
        def assess(self, *_):
            return TravelAssessment(status="VERIFIED", minutes=61, provider="test", checked_at=now)

    assert not feed([item], context, now, Routing()).top3

    class Within60:
        def assess(self, *_):
            return TravelAssessment(status="VERIFIED", minutes=60, provider="test", checked_at=now)

    assert len(feed([item], context, now, Within60()).top3) == 1


def test_simulated_time_does_not_qualify_live_events(content, context, now):
    assert not feed([content(content_type=ContentType.EVENT)], context, now, DemoRouting()).top3


def test_event_ends_before_arrival_excluded(content, context, now):
    class Routing:
        def assess(self, *_):
            return TravelAssessment(status="VERIFIED", minutes=40, checked_at=now)

    assert not feed(
        [content(content_type=ContentType.EVENT, expires_at=now + timedelta(minutes=20))],
        context,
        now,
        Routing(),
    ).top3


def test_alert_priority_route_namespace_and_expiry(context, now):
    items = demo_contents(now)
    nav = context.model_copy(
        update={"navigation_active": True, "route_link_ids": ["demo-link-1"], "route_link_namespace": "DEMO"}
    )
    result = feed(items, nav, now, DemoRouting())
    assert result.alerts[0].id == "mock:traffic"
    assert result.playback_order[0] == "mock:traffic"
    assert result.alerts[0].traffic.match_status == "LINK_MATCH"
    assert all(x.content_type != ContentType.TRAFFIC for x in result.top3 + result.queue)
    assert not feed(items, context, now, DemoRouting()).alerts
    wrong = nav.model_copy(update={"route_link_namespace": "OTHER"})
    assert not feed(items, wrong, now, DemoRouting()).alerts
    assert not feed(items, nav, now + timedelta(minutes=11), DemoRouting()).alerts


def test_proximity_only_not_urgent_and_stale_traffic_not_played(context, now):
    traffic = demo_contents(now)[-1]
    nav = FeedContext(
        **{
            **context.model_dump(),
            "navigation_active": True,
            "route_points": [{"latitude": 37.57, "longitude": 126.98}],
        }
    )
    assert not feed([traffic], nav, now).alerts
    nav.route_link_ids = ["demo-link-1"]
    nav.route_link_namespace = "DEMO"
    traffic.fetched_at = now - timedelta(minutes=11)
    assert not feed([traffic], nav, now).alerts


def test_eta_budget_affects_queue_not_screen(content, context, now):
    nav = context.model_copy(update={"navigation_active": True, "eta_minutes": 0.25})
    result = feed([content(str(i), title=f"개별 소식 {i}") for i in range(5)], nav, now)
    assert len(result.top3) == 3
    assert result.queue == []


def test_live_mock_mixed_and_empty_provenance(content, context, now):
    live = content()
    mock = demo_contents(now)[0]
    assert feed([live], context, now).data_mode == DataMode.LIVE
    assert feed([mock], context, now).data_mode == DataMode.MOCK
    assert feed([live, mock], context, now).data_mode == DataMode.MIXED
    empty = build_feed([], context, now, DataMode.MOCK)
    assert empty.data_mode == DataMode.MOCK
