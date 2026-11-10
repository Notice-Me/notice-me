"""Explicit, quota-bounded collection/validation. Does not print credentials or raw responses."""

import argparse
import asyncio
import json
import logging
from datetime import timedelta
from difflib import SequenceMatcher
from pathlib import Path

from .config import Settings
from .fixtures import demo_contents
from .models import utcnow
from .popups import load_confirmed_events
from .providers.base import ProviderError
from .providers.events import SeoulEvents, TourEvents
from .providers.news import NewsProvider
from .providers.seoul import SeoulCity, SeoulIncidents
from .recommendation import normalized_title
from .storage import Store

logging.getLogger("httpx").setLevel(logging.WARNING)


def news_keys(settings):
    return {
        "freenews": settings.freenews_api_key.get_secret_value(),
        "thenewsapi": settings.thenewsapi_token.get_secret_value(),
        "gnews": settings.gnews_api_key.get_secret_value(),
    }


def duplicate_ratio(rows):
    kept = []
    duplicates = 0
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


async def collect_public(settings: Settings, store: Store):
    now = utcnow()
    report = []
    providers = [
        SeoulEvents(settings.seoul_api_key.get_secret_value(), settings.http_timeout_seconds),
        SeoulCity(settings.seoul_api_key.get_secret_value(), settings.http_timeout_seconds),
        SeoulIncidents(settings.seoul_api_key.get_secret_value(), settings.http_timeout_seconds),
        TourEvents(settings.tour_api_key.get_secret_value(), settings.http_timeout_seconds),
    ]
    for provider in providers:
        try:
            items, meta = await provider.collect(now)
            store.upsert(items)
            store.record(provider.name, "SUCCESS", len(items), "OK")
            report.append(
                {
                    "provider": provider.name,
                    "status": "SUCCESS",
                    "http_status": provider.http.last_http_status,
                    "normalized_count": len(items),
                    "metadata": meta,
                    "valid_count_at_collection": sum(x.expires_at > now for x in items),
                    "items": [
                        {
                            "id": x.id,
                            "content_type": x.content_type.value,
                            "expires_at": x.expires_at.isoformat(),
                            "data_mode": x.data_mode.value,
                            "rights_status": x.rights_status.value,
                            "updated_at": x.updated_at.isoformat() if x.updated_at else None,
                        }
                        for x in items
                    ],
                }
            )
        except ProviderError as error:
            store.record(provider.name, "FAILED", 0, error.code)
            report.append(
                {
                    "provider": provider.name,
                    "status": "FAILED",
                    "code": error.code,
                    "http_status": error.http_status,
                    "normalized_count": 0,
                }
            )
    if settings.manual_events_path:
        items = load_confirmed_events(settings.manual_events_path)
        store.upsert(items)
        store.record("manual_events", "SUCCESS", len(items), "MANUAL_REVIEW_REQUIRED")
        report.append({"provider": "manual_events", "status": "SUCCESS", "normalized_count": len(items)})
    return report


async def collect_news(settings: Settings, store: Store, keyword: str):
    now = utcnow()
    outcomes = []
    # First-priority source only for ordinary ingestion; comparators are validation-only.
    provider = NewsProvider("freenews", news_keys(settings)["freenews"], settings.http_timeout_seconds)
    try:
        result = await provider.search(keyword, now - timedelta(days=7), now)
        items = provider.normalize(result["rows"], now, keyword)
        store.upsert(items)
        store.record("freenews", "SUCCESS", len(items), "RIGHTS_UNVERIFIED")
        outcomes.append(
            {
                "provider": "freenews",
                "status": "SUCCESS",
                "normalized_count": len(items),
                "sample_size": result["sample_size"],
            }
        )
    except ProviderError as error:
        store.record("freenews", "FAILED", 0, error.code)
        outcomes.append({"provider": "freenews", "status": "FAILED", "code": error.code})
    return outcomes


async def validate_news(settings: Settings):
    now = utcnow()
    results = []
    for name, key in news_keys(settings).items():
        provider = NewsProvider(name, key, settings.http_timeout_seconds)
        if not key:
            # One actual unauthenticated call verifies the auth barrier; zero articles is not inferred.
            try:
                await provider.search(
                    "애니메이션", now - timedelta(days=1), now, probe=True, include_details=False
                )
                probe = {"status": "UNAUTHENTICATED_RESPONSE", "http_status": provider.http.last_http_status}
            except ProviderError as error:
                probe = {"status": "FAILED", "code": error.code, "http_status": error.http_status}
            cases = [
                {
                    "keyword": word,
                    "window_hours": hours,
                    "status": "BLOCKED_NO_KEY",
                    "reported_total": None,
                    "sample_count": None,
                    "duplicate_sample_ratio": None,
                }
                for word in ("애니메이션", "과학 IT", "예술")
                for hours in (24, 168)
            ]
        else:
            probe, cases = None, []
            for word in ("애니메이션", "과학 IT", "예술"):
                for hours in (24, 168):
                    case = {"keyword": word, "window_hours": hours}
                    try:
                        result = await provider.search(
                            word, now - timedelta(hours=hours), now, include_details=False
                        )
                        rows = result["rows"]
                        case.update(
                            status="SUCCESS",
                            reported_total=result["reported_total"],
                            sample_count=len(rows),
                            has_more=result["has_more"],
                            duplicate_sample_ratio=duplicate_ratio(rows),
                            observed_fields=sorted(set().union(*(set(r) for r in rows))) if rows else [],
                        )
                    except ProviderError as error:
                        case.update(
                            status="FAILED",
                            code=error.code,
                            http_status=error.http_status,
                            reported_total=None,
                            sample_count=None,
                            duplicate_sample_ratio=None,
                        )
                    cases.append(case)
                    if case.get("code") == "RATE_LIMITED":
                        break
                if cases[-1].get("code") == "RATE_LIMITED":
                    break
        results.append(
            {
                "provider": name,
                "key_configured": bool(key),
                "unauthenticated_probe": probe,
                "cases": cases,
                "requests_made": provider.http.calls,
                "duplicate_method": "title normalization / similarity >=0.88 within first result page; not exact event identity",
                "coverage_note": "ko/kr absent from official filter lists; Korean keyword only, 12h delay"
                if name == "gnews"
                else "Authenticated coverage not measured without key",
            }
        )
    return results


async def run(args):
    settings = Settings()
    store = Store(settings.db_path)
    report = {"checked_at": utcnow().isoformat(), "results": []}
    if args.command == "seed":
        store.upsert(demo_contents(utcnow()))
        report["results"] = [{"provider": "fixtures", "status": "SUCCESS", "data_mode": "MOCK", "count": 8}]
    elif args.command == "ingest":
        report["results"] = await collect_public(settings, store)
        if args.keyword:
            report["news"] = await collect_news(settings, store, args.keyword)
    elif args.command == "validate":
        report["results"] = await collect_public(settings, store)
        report["news"] = await validate_news(settings)
        # TourAPI authentication barrier must be tested separately when no key is available.
        if not settings.tour_api_key.get_secret_value():
            provider = TourEvents("", settings.http_timeout_seconds)
            try:
                await provider.collect(utcnow(), probe=True)
                report["tour_unauthenticated_probe"] = {"status": "UNAUTHENTICATED_RESPONSE"}
            except ProviderError as error:
                report["tour_unauthenticated_probe"] = {
                    "status": "FAILED",
                    "code": error.code,
                    "http_status": error.http_status,
                }
        report["its"] = {
            "status": "NOT_CALLED",
            "reason": "NO_KEY_AND_CURRENT_OFFICIAL_ENDPOINT_DOC_UNREACHABLE",
        }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["seed", "ingest", "validate"])
    parser.add_argument("--keyword", help="Optional FreeNewsAPI keyword ingestion")
    parser.add_argument("--report", type=Path, help="Sanitized report path; no raw bodies or credential URLs")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
