"""Bounded news jobs: retain each outcome before moving to the next query."""

from datetime import timedelta
from difflib import SequenceMatcher

from .config import Settings
from .models import utcnow
from .providers.base import ProviderError, RequestBudget
from .providers.news import NewsProvider
from .recommendation import normalized_title
from .storage import Store


def news_keys(settings):
    return {
        "freenews": settings.freenews_api_key.get_secret_value(),
        "thenewsapi": settings.thenewsapi_token.get_secret_value(),
        "gnews": settings.gnews_api_key.get_secret_value(),
    }


def make_provider(settings, name, key, budget):
    return NewsProvider(
        name, key, settings.news_read_timeout_seconds, max_retries=settings.news_max_retries, budget=budget
    )


def duplicate_ratio(rows):
    kept, duplicates = [], 0
    for row in rows:
        title = normalized_title(row.get("title", ""))
        if title and any(
            title == old
            or (min(len(title), len(old)) >= 12 and SequenceMatcher(None, title, old).ratio() >= 0.88)
            for old in kept
        ):
            duplicates += 1
        elif title:
            kept.append(title)
    return duplicates / len(rows) if rows else None


def success_case(keyword, hours, result):
    rows = result["listing_rows"]
    more = result["has_more"]
    return {
        "keyword": keyword,
        "window_hours": hours,
        "status": "SUCCESS",
        "http_status": 200,
        "reported_total": result["reported_total"],
        "sample_count": len(rows),
        "provider_returned": result["provider_returned"],
        "page_size": result["page_size"],
        "has_more": more,
        "total_lower_bound": len(rows) + (1 if more is True else 0),
        "count_scope": "FIRST_PAGE_ONLY",
        "duplicate_sample_ratio": duplicate_ratio(rows),
        "observed_fields": result["observed_fields"],
        "attempts": result["attempts"],
    }


def error_case(keyword, hours, error, http):
    return {
        "keyword": keyword,
        "window_hours": hours,
        "status": "FAILED",
        "code": error.code,
        "http_status": error.http_status,
        "timeout_phase": error.timeout_phase,
        "reported_total": None,
        "sample_count": None,
        "duplicate_sample_ratio": None,
        "attempts": list(http.last_attempts),
    }


async def collect_news(settings: Settings, store: Store, keyword: str | list[str], *, budget=None):
    budget = budget or RequestBudget(settings.news_request_budget)
    provider = make_provider(settings, "freenews", news_keys(settings)["freenews"], budget)
    outcomes = []
    words = [keyword] if isinstance(keyword, str) else keyword
    for word in dict.fromkeys(words):
        now = utcnow()
        try:
            result = await provider.search(word, now - timedelta(days=7), now, include_details=False)
            case = success_case(word, 168, result)
            # Listing metadata and successful details are retained even if a sibling lookup failed.
            store.record_news_search("freenews", case, result["listing_rows"])
            result.update(await provider.hydrate(result["listing_rows"]))
            items = provider.normalize(result["rows"], now, word)
            store.upsert(items)
            status = "PARTIAL" if result.get("detail_errors") else "SUCCESS"
            store.record("freenews", status, len(items), "RIGHTS_UNVERIFIED")
            outcomes.append(
                {
                    **case,
                    "status": status,
                    "normalized_count": len(items),
                    "detail_errors": result.get("detail_errors", []),
                }
            )
        except ProviderError as error:
            case = error_case(word, 168, error, provider.http)
            store.record_news_search("freenews", case, [])
            store.record("freenews", "FAILED", 0, error.code)
            outcomes.append(case)
    return outcomes


async def validate_news(
    settings: Settings,
    *,
    providers=None,
    keywords=None,
    window_hours=None,
    store: Store | None = None,
    budget=None,
    checkpoint=None,
):
    budget = budget or RequestBudget(settings.news_request_budget)
    now = utcnow()
    reports = []
    for name, key in news_keys(settings).items():
        if providers and name not in providers:
            continue
        provider = make_provider(settings, name, key, budget)
        report = {
            "provider": name,
            "key_configured": bool(key),
            "unauthenticated_probe": None,
            "cases": [],
            "requests_made": 0,
            "duplicate_method": "title similarity >=0.88 within first result page; not exact event identity",
            "coverage_note": (
                "ko/kr filters unsupported; Korean keyword only, 12h delay"
                if name == "gnews"
                else "Authenticated query attempted; counts are returned-page observations, not corpus totals"
                if key
                else "Authenticated coverage not measured without key"
            ),
        }
        reports.append(report)
        if not key:
            try:
                await provider.search(
                    "애니메이션", now - timedelta(days=1), now, probe=True, include_details=False
                )
                report["unauthenticated_probe"] = {
                    "status": "UNAUTHENTICATED_RESPONSE",
                    "http_status": provider.http.last_http_status,
                }
            except ProviderError as error:
                report["unauthenticated_probe"] = {
                    "status": "FAILED",
                    "code": error.code,
                    "http_status": error.http_status,
                }
        for word in dict.fromkeys(keywords or ["애니메이션", "과학 IT", "예술"]):
            for hours in dict.fromkeys(window_hours or [24, 168]):
                rows = []
                if not key:
                    case = {
                        "keyword": word,
                        "window_hours": hours,
                        "status": "BLOCKED_NO_KEY",
                        "reported_total": None,
                        "sample_count": None,
                        "duplicate_sample_ratio": None,
                    }
                else:
                    try:
                        result = await provider.search(
                            word, now - timedelta(hours=hours), now, include_details=False
                        )
                        case = success_case(word, hours, result)
                        rows = result["listing_rows"]
                    except ProviderError as error:
                        case = error_case(word, hours, error, provider.http)
                # Commit before the next request so interruption/later failures cannot lose success.
                if store:
                    store.record_news_search(name, case, rows)
                report["cases"].append(case)
                report["requests_made"] = provider.http.calls
                report["quota_remaining_day"] = provider.http.quota_remaining
                if checkpoint:
                    checkpoint(reports)
    return reports
