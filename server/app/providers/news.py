from datetime import datetime, timedelta

import httpx

from ..llm import DeterministicLLM
from ..models import Content, ContentType, DataMode, RightsStatus, Verification
from .base import ProviderError, RequestBudget, SafeHTTP, parse_datetime, stable_id

ENDPOINTS = {
    "freenews": "https://api.freenewsapi.io/v1/news",
    "thenewsapi": "https://api.thenewsapi.com/v1/news/all",
    "gnews": "https://gnews.io/api/v4/search",
}


class NewsProvider:
    def __init__(
        self,
        name: str,
        key: str,
        timeout=20,
        transport=None,
        *,
        max_retries=1,
        budget: RequestBudget | None = None,
    ):
        if name not in ENDPOINTS:
            raise ValueError("Unknown news provider")
        self.name, self.key = name, key
        self.http = SafeHTTP(
            name,
            httpx.Timeout(timeout, connect=min(5, timeout), write=5, pool=5),
            transport,
            min_interval=0.6 if name == "freenews" else 1.1,
            max_retries=max_retries,
            budget=budget,
            total_timeout=30,
        )

    @staticmethod
    def metadata(row: dict) -> dict:
        # News metadata only: never retain article bodies, incipits, descriptions, or images.
        metadata = {
            k: row[k]
            for k in (
                "uuid",
                "title",
                "publisher",
                "published_at",
                "original_url",
                "url",
                "publishedAt",
                "source",
            )
            if k in row
        }
        if isinstance(metadata.get("source"), dict):
            metadata["source"] = {k: v for k, v in metadata["source"].items() if k in {"name", "url"}}
        return metadata

    async def search(
        self, keyword: str, since: datetime, until: datetime, *, probe=False, include_details=True
    ) -> dict:
        if not self.key and not probe:
            raise ProviderError(self.name, "MISSING_KEY")
        start, end = since.isoformat(), until.isoformat()
        headers = None
        if self.name == "freenews":
            params = {
                "language": "ko",
                "country": "KR",
                "in_title": keyword,
                "published_after": start,
                "published_before": end,
                "order_by": "recent",
            }
            headers = {"x-api-key": self.key} if self.key else {}
        elif self.name == "thenewsapi":
            params = {
                "api_token": self.key,
                "search": keyword,
                "language": "ko",
                "locale": "kr",
                "published_after": start,
                "published_before": end,
                "limit": 3,
            }
        else:
            # Current official supported-language/country lists omit ko/kr.
            # A Korean text query is permitted; don't invent unsupported structured filters.
            # Free tier is delayed 12 hours. Do not request the paid freshness window.
            end = (until - timedelta(hours=12)).isoformat()
            params = {
                "apikey": self.key,
                "q": keyword,
                "from": start,
                "to": end,
                "max": 10,
                "sortby": "publishedAt",
            }
        data = await self.http.json(ENDPOINTS[self.name], params=params, headers=headers)
        rows = data.get("articles") if self.name == "gnews" else data.get("data")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ProviderError(self.name, "SCHEMA_MISMATCH", 200)
        meta = data.get("meta", {})
        if not isinstance(meta, dict):
            raise ProviderError(self.name, "SCHEMA_MISMATCH", 200)
        result = {
            "rows": [self.metadata(row) for row in rows],
            "listing_rows": [self.metadata(row) for row in rows],
            "reported_total": data.get("totalArticles", meta.get("found")),
            "has_more": meta.get("has_more"),
            "sample_size": len(rows),
            "provider_returned": meta.get("returned"),
            "page_size": meta.get("page_size"),
            "observed_fields": sorted(set().union(*(set(r) for r in rows))) if rows else [],
            "attempts": list(self.http.last_attempts),
        }
        if self.name == "freenews" and include_details:
            detail = await self.hydrate(rows)
            result.update(detail)
        return result

    async def hydrate(self, rows: list[dict], *, limit=3) -> dict:
        """Resolve a bounded number of URLs; a failed article never discards successful siblings."""
        detailed, errors = [], []
        for row in rows[:limit]:
            if not row.get("uuid"):
                continue
            try:
                detail = await self.http.json(
                    "https://api.freenewsapi.io/v1/details",
                    params={"uuid": row["uuid"]},
                    headers={"x-api-key": self.key},
                )
                article = detail.get("data")
            except ProviderError as error:
                errors.append(
                    {
                        "uuid": row["uuid"],
                        "code": error.code,
                        "http_status": error.http_status,
                        "timeout_phase": error.timeout_phase,
                        "attempts": error.attempts,
                    }
                )
                if error.code in {
                    "RATE_LIMITED",
                    "REQUEST_BUDGET_EXHAUSTED",
                    "AUTH_REQUIRED",
                    "ACCESS_DENIED",
                }:
                    break
                continue
            if isinstance(article, dict):
                detailed.append(self.metadata(article))
            else:
                errors.append({"uuid": row["uuid"], "code": "SCHEMA_MISMATCH", "http_status": 200})
        return {"rows": detailed, "details_sample_size": len(detailed), "detail_errors": errors}

    def normalize(self, rows: list[dict], now: datetime, keyword: str) -> list[Content]:
        items = []
        for row in rows:
            url = row.get("original_url") if self.name == "freenews" else row.get("url")
            published = parse_datetime(
                row.get("publishedAt") if self.name == "gnews" else row.get("published_at")
            )
            if not url or not published or not row.get("title"):
                continue
            source = row.get("source")
            if isinstance(source, dict):
                source = source.get("name")
            # Descriptions are evaluated by validation, but not redistributed without license review.
            try:
                items.append(
                    Content(
                        id=stable_id(self.name, url),
                        content_type=ContentType.NEWS,
                        title=row["title"],
                        brief="",
                        source_name=row.get("publisher") or source or self.name,
                        source_url=url,
                        published_at=published,
                        updated_at=None,
                        fetched_at=now,
                        expires_at=published + timedelta(days=7),
                        interest_tags=DeterministicLLM().classify(row["title"] + " " + keyword),
                        rights_status=RightsStatus.LICENSE_UNVERIFIED,
                        verification_status=Verification.VERIFIED,
                        data_mode=DataMode.LIVE,
                        provenance=f"{self.name}:official_api;metadata_only;classification=MOCK",
                    )
                )
            except ValueError:
                continue
        return items
