import asyncio
import copy
import json
from types import SimpleNamespace

import httpx
import pytest

from app import cli, news_jobs
from app.config import Settings
from app.providers.base import RequestBudget
from app.providers.news import NewsProvider
from app.storage import Store


def settings(tmp_path):
    return Settings(_env_file=None, db_path=tmp_path / "test.db", freenews_api_key="fake")


def patch_provider(monkeypatch, respond):
    def factory(config, name, key, budget):
        p = NewsProvider(name, key, transport=httpx.MockTransport(respond), max_retries=0, budget=budget)
        p.http.min_interval = 0
        return p

    monkeypatch.setattr(news_jobs, "make_provider", factory)


async def test_success_saved_before_next_failure_and_checkpoint_survives(tmp_path, monkeypatch):
    config = settings(tmp_path)
    store = Store(config.db_path)
    report = tmp_path / "report.json"

    def respond(request):
        if request.url.params["in_title"] == "good":
            return httpx.Response(
                200,
                json={
                    "data": [{"uuid": "one", "title": "예술", "body": "NOT_STORED"}],
                    "meta": {"returned": 1, "page_size": 10, "has_more": False},
                },
            )
        saved = store.news_searches("freenews")
        assert saved[0]["status"] == "SUCCESS" and len(saved[0]["article_metadata"]) == 1
        assert json.loads(report.read_text(encoding="utf8"))[0]["cases"][0]["sample_count"] == 1
        return httpx.Response(500)

    patch_provider(monkeypatch, respond)
    snapshots = []

    def checkpoint(results):
        snapshots.append(copy.deepcopy(results))
        cli.write_report(report, results)

    result = await news_jobs.validate_news(
        config,
        providers=["freenews"],
        keywords=["good", "bad"],
        window_hours=[24],
        store=store,
        checkpoint=checkpoint,
    )
    assert [x["status"] for x in result[0]["cases"]] == ["SUCCESS", "FAILED"]
    assert [len(x[0]["cases"]) for x in snapshots] == [1, 2]
    assert "NOT_STORED" not in json.dumps(store.news_searches("freenews"))
    assert len(store.news_searches("freenews")[0]["article_metadata"]) == 1


async def test_interruption_keeps_previous_success_in_db_and_json(tmp_path, monkeypatch):
    config = settings(tmp_path)
    store = Store(config.db_path)
    report = tmp_path / "report.json"

    def respond(request):
        if request.url.params["in_title"] == "interrupt":
            raise asyncio.CancelledError()
        return httpx.Response(
            200, json={"data": [{"uuid": "one", "title": "예술"}], "meta": {"has_more": False}}
        )

    patch_provider(monkeypatch, respond)
    with pytest.raises(asyncio.CancelledError):
        await news_jobs.validate_news(
            config,
            providers=["freenews"],
            keywords=["good", "interrupt"],
            window_hours=[24],
            store=store,
            checkpoint=lambda r: cli.write_report(report, r),
        )
    assert store.news_searches("freenews")[0]["status"] == "SUCCESS"
    assert len(json.loads(report.read_text(encoding="utf8"))[0]["cases"]) == 1


@pytest.mark.parametrize("more,count,lower", [(False, 0, 0), (False, 5, 5), (True, 10, 11)])
async def test_first_page_count_not_misrepresented_as_total(tmp_path, monkeypatch, more, count, lower):
    patch_provider(
        monkeypatch,
        lambda r: httpx.Response(
            200,
            json={
                "data": [{"uuid": str(i), "title": "예술"} for i in range(count)],
                "meta": {"returned": count, "page_size": 10, "has_more": more},
            },
        ),
    )
    result = await news_jobs.validate_news(
        settings(tmp_path), providers=["freenews"], keywords=["art"], window_hours=[24]
    )
    case = result[0]["cases"][0]
    assert case["sample_count"] == count and case["provider_returned"] == count
    assert case["reported_total"] is None and case["total_lower_bound"] == lower
    assert case["count_scope"] == "FIRST_PAGE_ONLY"
    assert "without key" not in result[0]["coverage_note"]


async def test_later_keyword_failure_does_not_delete_ingested_content(tmp_path, monkeypatch, now):
    config = settings(tmp_path)
    store = Store(config.db_path)

    def respond(request):
        if request.url.path.endswith("/news"):
            if request.url.params["in_title"] == "bad":
                return httpx.Response(500)
            return httpx.Response(
                200, json={"data": [{"uuid": "one", "title": "예술"}], "meta": {"has_more": False}}
            )
        return httpx.Response(
            200,
            json={
                "data": {
                    "uuid": "one",
                    "title": "예술",
                    "published_at": now.isoformat(),
                    "publisher": "Example",
                    "original_url": "https://paper.example/one",
                    "body": "NOT_STORED",
                }
            },
        )

    patch_provider(monkeypatch, respond)
    monkeypatch.setattr(news_jobs, "utcnow", lambda: now)
    result = await news_jobs.collect_news(config, store, ["good", "bad"])
    assert [x["status"] for x in result] == ["SUCCESS", "FAILED"]
    saved = store.all("live")
    assert len(saved) == 1 and saved[0].rights_status.value == "LICENSE_UNVERIFIED"
    assert "NOT_STORED" not in saved[0].model_dump_json()


async def test_shared_attempt_budget_stops_remaining_keywords_without_calls(tmp_path, monkeypatch):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"data": [], "meta": {"has_more": False}})

    patch_provider(monkeypatch, respond)
    result = await news_jobs.validate_news(
        settings(tmp_path),
        providers=["freenews"],
        keywords=["a", "b"],
        window_hours=[24],
        budget=RequestBudget(1),
    )
    assert len(requests) == result[0]["requests_made"] == 1
    assert result[0]["cases"][1]["code"] == "REQUEST_BUDGET_EXHAUSTED"
    assert result[0]["cases"][1]["http_status"] is None


@pytest.mark.parametrize("selected_providers", [None, ["freenews"]])
async def test_news_only_cli_never_collects_public_data(tmp_path, monkeypatch, capsys, selected_providers):
    config = settings(tmp_path)
    monkeypatch.setattr(cli, "Settings", lambda: config)

    async def fail(*args):
        pytest.fail("Public API collection must not run")

    monkeypatch.setattr(cli, "collect_public", fail)
    patch_provider(monkeypatch, lambda r: httpx.Response(200, json={"data": [], "meta": {"has_more": False}}))
    args = SimpleNamespace(
        command="validate-news",
        keyword=["art"],
        provider=selected_providers,
        window_hours=[24],
        max_requests=1,
        report=tmp_path / "report.json",
    )
    await cli.run(args)
    result = json.loads(args.report.read_text(encoding="utf8"))
    assert result["results"] == [] and len(result["news"]) == 1
    assert result["news_request_budget"]["used"] == 1
    assert result["news"][0]["cases"][0]["status"] == "SUCCESS"


async def test_ingest_retains_listing_even_if_details_interrupted(tmp_path, monkeypatch):
    config = settings(tmp_path)
    store = Store(config.db_path)

    def respond(request):
        if request.url.path.endswith("/details"):
            assert store.news_searches("freenews")[0]["sample_count"] == 1
            raise asyncio.CancelledError()
        return httpx.Response(
            200, json={"data": [{"uuid": "one", "title": "예술"}], "meta": {"has_more": False}}
        )

    patch_provider(monkeypatch, respond)
    with pytest.raises(asyncio.CancelledError):
        await news_jobs.collect_news(config, store, "art")
    assert store.news_searches("freenews")[0]["article_metadata"][0]["uuid"] == "one"


async def test_duplicate_query_options_do_not_spend_extra_requests(tmp_path, monkeypatch):
    patch_provider(monkeypatch, lambda r: httpx.Response(200, json={"data": [], "meta": {"has_more": False}}))
    budget = RequestBudget(1)
    result = await news_jobs.validate_news(
        settings(tmp_path),
        providers=["freenews"],
        keywords=["art", "art"],
        window_hours=[24, 24],
        budget=budget,
    )
    assert len(result[0]["cases"]) == 1 and budget.used == 1


async def test_ingest_news_cli_does_not_call_public_providers(tmp_path, monkeypatch, capsys):
    config = settings(tmp_path)
    monkeypatch.setattr(cli, "Settings", lambda: config)

    async def fail(*args):
        pytest.fail("No unrelated public API calls")

    monkeypatch.setattr(cli, "collect_public", fail)
    patch_provider(monkeypatch, lambda r: httpx.Response(200, json={"data": [], "meta": {"has_more": False}}))
    args = SimpleNamespace(
        command="ingest-news",
        keyword=["art"],
        provider=None,
        window_hours=None,
        max_requests=1,
        report=tmp_path / "report.json",
    )
    await cli.run(args)
    result = json.loads(args.report.read_text(encoding="utf8"))
    assert result["results"] == [] and result["news"][0]["normalized_count"] == 0
    assert result["news_request_budget"]["used"] == 1
