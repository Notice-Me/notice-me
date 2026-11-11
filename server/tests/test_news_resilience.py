import asyncio
import json

import httpx
import pytest

from app.providers.base import ProviderError, RequestBudget, SafeHTTP
from app.providers.news import NewsProvider


@pytest.fixture
def fast_backoff(monkeypatch):
    delays = []

    async def sleep(delay):
        delays.append(delay)

    monkeypatch.setattr("app.providers.base.asyncio.sleep", sleep)
    monkeypatch.setattr("app.providers.base.random.uniform", lambda a, b: 0.125)
    return delays


async def test_read_timeout_retry_records_phase_and_obeys_budget(fast_backoff):
    requests = []

    def respond(request):
        requests.append(request)
        if len(requests) == 1:
            raise httpx.ReadTimeout("key=do-not-leak", request=request)
        return httpx.Response(200, json={"data": []})

    budget = RequestBudget(2)
    http = SafeHTTP("freenews", transport=httpx.MockTransport(respond), max_retries=1, budget=budget)
    result = await http.json("https://provider.invalid/news", headers={"x-api-key": "secret"})
    assert result == {"data": []} and http.calls == budget.used == 2
    assert http.last_attempts[0]["timeout_phase"] == "read"
    assert http.last_attempts[0]["http_status"] is None
    assert http.last_attempts[1]["code"] == "SUCCESS"
    assert fast_backoff == [1.125]
    assert "do-not-leak" not in json.dumps(http.last_attempts)


@pytest.mark.parametrize(
    "kind,phase",
    [
        (httpx.ConnectTimeout, "connect"),
        (httpx.ReadTimeout, "read"),
        (httpx.WriteTimeout, "write"),
        (httpx.PoolTimeout, "pool"),
    ],
)
async def test_each_timeout_phase_is_distinguishable(kind, phase):
    def respond(request):
        raise kind("sensitive request URL", request=request)

    http = SafeHTTP("freenews", transport=httpx.MockTransport(respond))
    with pytest.raises(ProviderError) as caught:
        await http.get("https://provider.invalid/news")
    assert caught.value.timeout_phase == phase and caught.value.code == "TIMEOUT"
    assert http.calls == 1 and http.last_http_status is None


@pytest.mark.parametrize("status", [502, 503, 504])
async def test_only_selected_server_failures_are_retried(status, fast_backoff):
    codes = iter([status, 200])
    http = SafeHTTP(
        "test", transport=httpx.MockTransport(lambda r: httpx.Response(next(codes))), max_retries=1
    )
    assert (await http.get("https://provider.invalid/news")).status_code == 200
    assert http.calls == 2 and len(fast_backoff) == 1


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500])
async def test_deterministic_or_auth_quota_failures_not_retried(status, fast_backoff):
    http = SafeHTTP("test", transport=httpx.MockTransport(lambda r: httpx.Response(status)), max_retries=1)
    with pytest.raises(ProviderError):
        await http.get("https://provider.invalid/news")
    assert http.calls == 1 and fast_backoff == []


async def test_budget_limits_retries_and_next_keyword(fast_backoff):
    budget = RequestBudget(1)
    http = SafeHTTP(
        "test", transport=httpx.MockTransport(lambda r: httpx.Response(503)), max_retries=1, budget=budget
    )
    with pytest.raises(ProviderError) as first:
        await http.get("https://provider.invalid/news")
    assert first.value.http_status == 503 and first.value.attempts == 1
    with pytest.raises(ProviderError, match="REQUEST_BUDGET_EXHAUSTED") as second:
        await http.get("https://provider.invalid/news")
    assert second.value.http_status is None and second.value.attempts == 0
    assert budget.used == http.calls == 1 and fast_backoff == []


async def test_quota_zero_stops_without_fabricating_http429():
    http = SafeHTTP(
        "test",
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, headers={"x-ratelimit-remaining-day": "0"})
        ),
    )
    await http.get("https://provider.invalid/news")
    with pytest.raises(ProviderError) as caught:
        await http.get("https://provider.invalid/news")
    assert caught.value.code == "RATE_LIMITED" and caught.value.http_status is None
    assert http.calls == 1


async def test_total_deadline_and_failed_attempt_does_not_reuse_old_status():
    async def never_returns(request):
        await asyncio.Event().wait()

    http = SafeHTTP("test", transport=httpx.MockTransport(never_returns), total_timeout=0.01)
    http.last_http_status = 200
    with pytest.raises(ProviderError) as caught:
        await http.get("https://provider.invalid/news")
    assert caught.value.timeout_phase == "total" and caught.value.http_status is None
    assert http.last_http_status is None


async def test_invalid_json_not_retried(fast_backoff):
    http = SafeHTTP(
        "test", transport=httpx.MockTransport(lambda r: httpx.Response(200, text="bad json")), max_retries=1
    )
    with pytest.raises(ProviderError, match="INVALID_JSON"):
        await http.json("https://provider.invalid/news")
    assert http.calls == 1 and fast_backoff == []


async def test_decode_error_after_recovery_preserves_actual_attempt_count(fast_backoff):
    requests = []

    def respond(request):
        requests.append(request)
        if len(requests) == 1:
            raise httpx.ReadTimeout("not logged", request=request)
        return httpx.Response(200, text="invalid JSON")

    http = SafeHTTP("test", transport=httpx.MockTransport(respond), max_retries=1)
    with pytest.raises(ProviderError, match="INVALID_JSON") as caught:
        await http.json("https://provider.invalid/news")
    assert caught.value.attempts == http.calls == 2


async def test_partial_details_keep_listing_successful_siblings_and_rights(now):
    def respond(request):
        if request.url.path.endswith("/news"):
            return httpx.Response(
                200,
                json={
                    "data": [{"uuid": x, "title": "예술"} for x in "abc"],
                    "meta": {"returned": 3, "has_more": False},
                },
            )
        uid = request.url.params["uuid"]
        if uid == "b":
            return httpx.Response(500, json={"error": "Internal Server Error"})
        return httpx.Response(
            200,
            json={
                "data": {
                    "uuid": uid,
                    "title": "예술 소식 " + uid,
                    "publisher": "Example",
                    "published_at": now.isoformat(),
                    "original_url": "https://paper.example/" + uid,
                    "body": "DO_NOT_RETAIN_BODY",
                    "incipit": "DO_NOT_RETAIN_SUMMARY",
                }
            },
        )

    provider = NewsProvider("freenews", "fake", transport=httpx.MockTransport(respond))
    provider.http.min_interval = 0
    result = await provider.search("예술", now, now)
    assert result["sample_size"] == 3 and len(result["listing_rows"]) == 3
    assert {r["uuid"] for r in result["rows"]} == {"a", "c"}
    assert result["detail_errors"][0]["http_status"] == 500
    assert "DO_NOT_RETAIN" not in json.dumps(result)
    items = provider.normalize(result["rows"], now, "예술")
    assert len(items) == 2 and all(
        x.rights_status.value == "LICENSE_UNVERIFIED" and x.brief == "" for x in items
    )


def test_metadata_whitelist_removes_nested_body():
    result = NewsProvider.metadata(
        {
            "title": "news",
            "body": "bad",
            "description": "bad",
            "source": {"name": "publisher", "url": "https://publisher.example/", "body": "bad"},
        }
    )
    assert result == {"title": "news", "source": {"name": "publisher", "url": "https://publisher.example/"}}


def test_news_timeout_profile_has_separate_connect_read_and_total_limits():
    provider = NewsProvider("freenews", "fake")
    assert provider.http.timeout.read == 20 and provider.http.timeout.connect == 5
    assert provider.http.timeout.write == provider.http.timeout.pool == 5
    assert provider.http.total_timeout == 30 and provider.http.max_retries == 1


@pytest.mark.parametrize("payload", [{"data": [None], "meta": {}}, {"data": [], "meta": []}])
async def test_malformed_listing_is_a_provider_error_not_batch_crash(now, payload):
    provider = NewsProvider(
        "freenews", "fake", transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload))
    )
    with pytest.raises(ProviderError, match="SCHEMA_MISMATCH"):
        await provider.search("art", now, now, include_details=False)
    assert provider.http.calls == 1
