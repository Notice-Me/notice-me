import asyncio
from datetime import UTC, datetime

import httpx
import pytest

from app import cli
from app.config import Settings
from app.models import DataMode, FeedContext, Verification
from app.providers.base import ProviderError, stable_id
from app.providers.events import TourEvents
from app.recommendation import build_feed
from app.rights import tts_allowed
from app.storage import Store


def row(identifier="one", **changes):
    return {
        "contentid": identifier,
        "contenttypeid": "15",
        "title": "테스트 예술 행사",
        "eventstartdate": "20261101",
        "eventenddate": "20261130",
        "progresstype": "선택안함",
        "cpyrhtDivCd": "Type1",
        "mapx": "127.0",
        "mapy": "37.5",
        "addr1": "공개 행사 장소",
        "createdtime": "20260101090000",
        "modifiedtime": "20261110150000",
        **changes,
    }


def response(rows, *, total=None, page=1, size=50):
    return httpx.Response(
        200,
        json={
            "response": {
                "header": {"resultCode": "0000"},
                "body": {
                    "items": {"item": rows},
                    "totalCount": len(rows) if total is None else total,
                    "numOfRows": size,
                    "pageNo": page,
                },
            }
        },
    )


def provider(respond, **kwargs):
    p = TourEvents("test-key-never-live", transport=httpx.MockTransport(respond), **kwargs)
    p.http.min_interval = 0
    return p


@pytest.mark.parametrize(
    ("progress", "reason"),
    [
        (None, None),
        ("", None),
        ("선택안함", None),
        (" 선택안함 ", None),
        ("취소", "CANCELLED"),
        ("행사연기", "POSTPONED"),
        ("0", "UNKNOWN_PROGRESS_TYPE"),
        (0, "UNKNOWN_PROGRESS_TYPE"),
        ("진행중", "UNKNOWN_PROGRESS_TYPE"),
    ],
)
def test_progress_is_not_a_truthy_cancellation_flag(now, progress, reason):
    p = TourEvents("test")
    items, decisions = p.normalize([row(progresstype=progress)], now)
    assert bool(items) == (reason is None)
    assert decisions[0]["reasons"] == ([reason] if reason else [])


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"eventstartdate": "bad"}, "INVALID_START_DATE"),
        ({"eventenddate": "20260230"}, "INVALID_END_DATE"),
        ({"eventenddate": "2026111"}, "INVALID_END_DATE"),
        ({"eventstartdate": "20261201"}, "END_BEFORE_START"),
        ({"eventenddate": "20261110"}, "EXPIRED_EVENT"),
        ({"eventstartdate": "20270501", "eventenddate": "20270503"}, "OUTSIDE_HORIZON"),
        ({"contentid": ""}, "MISSING_CONTENT_ID"),
        ({"title": None}, "INVALID_CONTENT_FIELDS"),
    ],
)
def test_per_row_exclusions_have_no_silent_drop(now, changes, reason):
    items, decisions = TourEvents("test").normalize([row(**changes)], now)
    assert items == [] and reason in decisions[0]["reasons"]


async def test_kst_window_keeps_long_ongoing_and_tomorrow_is_upcoming():
    now = datetime(2026, 11, 10, 15, 5, tzinfo=UTC)  # Nov11 00:05 KST
    captured = []

    def respond(request):
        captured.append(dict(request.url.params))
        return response([row(eventstartdate="20260101"), row("next", eventstartdate="20261112")])

    items, meta = await provider(respond).collect(now)
    assert captured[0]["eventStartDate"] == "20261111"
    assert captured[0]["eventEndDate"] == "20270209" and captured[0]["arrange"] == "C"
    assert captured[0]["numOfRows"] == "50" and captured[0]["pageNo"] == "1"
    assert meta["ongoing_count"] == meta["upcoming_count"] == 1
    assert meta["coverage_complete"] and len(items) == 2
    assert items[0].expires_at.isoformat() == "2026-11-30T15:00:00+00:00"
    assert items[0].fetched_at == now and items[0].updated_at != now


async def test_walks_pages_once_and_deduplicates(now):
    calls = []

    def respond(request):
        page = int(request.url.params["pageNo"])
        calls.append(page)
        return response(
            [row("one"), row("two")] if page == 1 else [row("two"), row("three")], total=4, page=page, size=2
        )

    items, meta = await provider(respond, page_size=2).collect(now)
    assert calls == [1, 2] and len(items) == 3 and meta["raw_count"] == 4
    assert meta["duplicate_row_count"] == 1 and not meta["coverage_complete"]
    assert "serviceKey" not in str(meta) and "test-key-never-live" not in str(meta)


@pytest.mark.parametrize(
    ("limits", "calls", "stop"),
    [
        ({"max_pages": 1}, 1, "PAGE_LIMIT"),
        ({"request_budget": 1}, 1, "REQUEST_BUDGET_EXHAUSTED"),
    ],
)
async def test_limits_are_truthful_partial_collection(now, limits, calls, stop):
    p = provider(lambda r: response([row()], total=268, page=int(r.url.params["pageNo"])), **limits)
    items, meta = await p.collect(now)
    assert len(items) == 1 and meta["requests_made"] == calls
    assert meta["collection_status"] == "PARTIAL" and meta["stop_reason"] == stop
    assert not meta["coverage_complete"]


@pytest.mark.parametrize("failure", ["timeout", "invalid_schema", "quota_xml"])
async def test_later_failure_retains_page_and_never_retries(now, tmp_path, failure):
    store = Store(tmp_path / "test.db")

    def respond(request):
        if request.url.params["pageNo"] == "1":
            return response([row()], total=100)
        assert len(store.event_pages("tourapi")) == len(store.all("live")) == 1
        if failure == "timeout":
            raise httpx.ReadTimeout("must not print credentials", request=request)
        if failure == "quota_xml":
            return httpx.Response(
                200,
                text="<OpenAPI_ServiceResponse><returnReasonCode>22</returnReasonCode></OpenAPI_ServiceResponse>",
            )
        return httpx.Response(200, json={"response": {"header": {"resultCode": "0000"}, "body": []}})

    p = provider(respond)
    items, meta = await p.collect(
        now, checkpoint=lambda items, page: store.save_event_page("tourapi", items, page)
    )
    assert len(items) == 1 and p.http.calls == 2 and meta["collection_status"] == "PARTIAL"
    assert (
        meta["stop_reason"]
        == {"timeout": "TIMEOUT", "invalid_schema": "SCHEMA_MISMATCH", "quota_xml": "RATE_LIMITED"}[failure]
    )


async def test_cancellation_of_task_keeps_completed_page(now, tmp_path):
    store = Store(tmp_path / "test.db")

    def respond(request):
        if request.url.params["pageNo"] == "2":
            raise asyncio.CancelledError()
        return response([row()], total=100)

    with pytest.raises(asyncio.CancelledError):
        await provider(respond).collect(
            now, checkpoint=lambda items, page: store.save_event_page("tourapi", items, page)
        )
    assert len(store.all("live")) == len(store.event_pages("tourapi")) == 1


async def test_refreshed_cancellation_quarantines_previous_content(now, tmp_path):
    store = Store(tmp_path / "test.db")
    existing, _ = TourEvents("test").normalize([row()], now)
    store.upsert(existing)
    items, _ = await provider(lambda r: response([row(progresstype="취소")])).collect(
        now, checkpoint=lambda items, page: store.save_event_page("tourapi", items, page)
    )
    assert items == []
    saved = store.get(stable_id("tour-event", "one"), "live")
    assert (
        saved is not None and saved.verification_status == Verification.UNVERIFIED and not tts_allowed(saved)
    )


async def test_conflicting_later_row_cannot_reenable_cancelled_event(now, tmp_path):
    store = Store(tmp_path / "test.db")

    def respond(request):
        page = int(request.url.params["pageNo"])
        return response([row(progresstype="취소" if page == 2 else "선택안함")], total=3, page=page, size=1)

    items, _ = await provider(respond, page_size=1).collect(
        now, checkpoint=lambda items, page: store.save_event_page("tourapi", items, page)
    )
    store.upsert(items)  # final CLI upsert must not undo quarantine
    assert items == [] and store.all("live")[0].verification_status == Verification.UNVERIFIED


@pytest.mark.parametrize("empty", ["", {}, {"item": ""}, {"item": []}])
async def test_empty_page_finishes_without_extra_calls(now, empty):
    p = provider(
        lambda r: httpx.Response(
            200,
            json={"response": {"header": {"resultCode": "0000"}, "body": {"items": empty, "totalCount": 0}}},
        )
    )
    items, meta = await p.collect(now)
    assert items == [] and p.http.calls == 1 and meta["coverage_complete"]


async def test_valid_tour_metadata_is_not_permission_to_recommend_or_speak(now):
    p = provider(lambda r: response([row(cpyrhtDivCd="Type3"), row("unknown", cpyrhtDivCd="")]))
    items, meta = await p.collect(now)
    assert len(items) == 2 and meta["ongoing_count"] == 2
    assert all(x.rights_status.value == "LICENSE_UNVERIFIED" and x.brief == "" for x in items)
    feed = build_feed(items, FeedContext(lat=37.57, lon=126.98, interests=["art"]), now, DataMode.LIVE)
    assert not (feed.top3 or feed.queue or feed.alerts)
    assert any(x.code == "DRIVING_TIME_UNVERIFIED" for x in feed.diagnostics)


async def test_cli_tour_only_uses_limits_and_persists_page(now, tmp_path, monkeypatch):
    config = Settings(_env_file=None, db_path=tmp_path / "test.db", tour_api_key="test-key-never-live")

    def factory(key, timeout, **kwargs):
        return provider(lambda r: response([row()]), **kwargs)

    monkeypatch.setattr(cli, "TourEvents", factory)
    monkeypatch.setattr(cli, "utcnow", lambda: now)
    store = Store(config.db_path)
    result = await cli.collect_public(config, store, selected=["tourapi"])
    assert len(result) == 1 and result[0]["valid_count_at_collection"] == 1
    assert len(store.event_pages("tourapi")) == len(store.all("live")) == 1


async def test_missing_key_never_calls_api(now):
    p = TourEvents("", transport=httpx.MockTransport(lambda r: pytest.fail("No key: no network")))
    with pytest.raises(ProviderError, match="MISSING_KEY"):
        await p.collect(now)


async def test_last_page_numofrows_is_return_count_not_page_stride(now):
    calls = []

    def respond(request):
        page = int(request.url.params["pageNo"])
        calls.append(page)
        assert page <= 2, "The complete 77 records must not trigger page3"
        count = 50 if page == 1 else 27
        return response(
            [row(str((page - 1) * 50 + n)) for n in range(count)], total=77, page=page, size=count
        )

    items, meta = await provider(respond, request_budget=2).collect(now)
    assert calls == [1, 2] and len(items) == meta["raw_count"] == 77
    assert meta["coverage_complete"] and meta["collection_status"] == "SUCCESS"


async def test_empty_before_reported_total_is_not_complete(now):
    p = provider(lambda r: response([], total=77, size=0))
    items, meta = await p.collect(now)
    assert items == [] and not meta["coverage_complete"] and meta["stop_reason"] == "EMPTY_PAGE_BEFORE_TOTAL"


async def test_changing_total_is_not_an_atomic_complete_snapshot(now):
    def respond(request):
        page = int(request.url.params["pageNo"])
        return response([row(str(page))], total=3 if page == 1 else 2, page=page, size=1)

    _, meta = await provider(respond, page_size=1).collect(now)
    assert meta["requests_made"] == 2 and meta["totals_changed_during_collection"]
    assert not meta["coverage_complete"] and meta["collection_status"] == "PARTIAL"
