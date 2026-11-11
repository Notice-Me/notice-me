"""Explicit, quota-bounded collection/validation. Does not print credentials or raw responses."""

import argparse
import asyncio
import json
import logging
from pathlib import Path

from .config import Settings
from .fixtures import demo_contents
from .models import utcnow
from .news_jobs import collect_news, validate_news
from .popups import load_confirmed_events
from .providers.base import ProviderError, RequestBudget
from .providers.events import SeoulEvents, TourEvents
from .providers.seoul import SeoulCity, SeoulIncidents
from .storage import Store

logging.getLogger("httpx").setLevel(logging.WARNING)


async def collect_public(settings: Settings, store: Store, selected=None):
    now = utcnow()
    report = []
    providers = [
        SeoulEvents(settings.seoul_api_key.get_secret_value(), settings.http_timeout_seconds),
        SeoulCity(settings.seoul_api_key.get_secret_value(), settings.http_timeout_seconds),
        SeoulIncidents(settings.seoul_api_key.get_secret_value(), settings.http_timeout_seconds),
        TourEvents(settings.tour_api_key.get_secret_value(), settings.http_timeout_seconds),
    ]
    for provider in providers:
        if selected is not None and provider.name not in selected:
            continue
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
    if settings.manual_events_path and (selected is None or "manual_events" in selected):
        items = load_confirmed_events(settings.manual_events_path)
        store.upsert(items)
        store.record("manual_events", "SUCCESS", len(items), "MANUAL_REVIEW_REQUIRED")
        report.append({"provider": "manual_events", "status": "SUCCESS", "normalized_count": len(items)})
    return report


def write_report(path, report):
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)


async def run(args):
    settings = Settings()
    store = Store(settings.db_path)
    report = {"checked_at": utcnow().isoformat(), "results": []}
    budget = RequestBudget(args.max_requests or settings.news_request_budget)

    def checkpoint(news):
        report["news"] = news
        report["news_request_budget"] = {"limit": budget.limit, "used": budget.used}
        write_report(args.report, report)

    options = {
        "providers": args.provider or (["freenews"] if args.command == "validate-news" else None),
        "keywords": args.keyword,
        "window_hours": args.window_hours,
        "store": store,
        "budget": budget,
        "checkpoint": checkpoint,
    }
    if args.command == "seed":
        store.upsert(demo_contents(utcnow()))
        report["results"] = [{"provider": "fixtures", "status": "SUCCESS", "data_mode": "MOCK", "count": 8}]
    elif args.command in {"ingest", "ingest-news"}:
        if args.command == "ingest":
            report["results"] = await collect_public(
                settings, store, selected=getattr(args, "public_provider", None)
            )
        if args.keyword:
            report["news"] = await collect_news(settings, store, args.keyword, budget=budget)
    elif args.command == "validate-news":
        report["news"] = await validate_news(settings, **options)
    elif args.command == "validate":
        report["results"] = await collect_public(settings, store)
        report["news"] = await validate_news(settings, **options)
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
    report["news_request_budget"] = {"limit": budget.limit, "used": budget.used}
    write_report(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["seed", "ingest", "validate", "validate-news", "ingest-news"])
    parser.add_argument("--keyword", action="append", help="Repeat for multiple explicit keywords")
    parser.add_argument(
        "--provider",
        action="append",
        choices=["freenews", "thenewsapi", "gnews"],
        help="Restrict news validation; validate-news skips public API calls",
    )
    parser.add_argument("--window-hours", action="append", type=int, choices=[24, 168])
    parser.add_argument(
        "--public-provider",
        action="append",
        choices=["seoul_events", "seoul_city", "seoul_incidents", "tourapi", "manual_events"],
        help="ingest only: collect selected public sources instead of all sources",
    )
    parser.add_argument(
        "--max-requests", type=int, help="News HTTP attempt budget, including retries/details (1..100)"
    )
    parser.add_argument("--report", type=Path, help="Sanitized report path; no raw bodies or credential URLs")
    args = parser.parse_args()
    if args.max_requests is not None and not 1 <= args.max_requests <= 100:
        parser.error("--max-requests must be between 1 and 100")
    if args.command == "ingest-news" and not args.keyword:
        parser.error("ingest-news requires at least one --keyword")
    if args.public_provider and args.command != "ingest":
        parser.error("--public-provider is supported only with ingest")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
