from datetime import datetime, timedelta

from ..llm import DeterministicLLM
from ..models import Content, ContentType, DataMode, RightsStatus, Verification
from .base import ProviderError, SafeHTTP, parse_datetime, stable_id

ENDPOINTS = {
    "freenews": "https://api.freenewsapi.io/v1/news",
    "thenewsapi": "https://api.thenewsapi.com/v1/news/all",
    "gnews": "https://gnews.io/api/v4/search",
}


class NewsProvider:
    def __init__(self, name: str, key: str, timeout=10, transport=None):
        if name not in ENDPOINTS:
            raise ValueError("Unknown news provider")
        self.name, self.key = name, key
        self.http = SafeHTTP(name, timeout, transport, min_interval=0.6 if name == "freenews" else 1.1)

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
        if not isinstance(rows, list):
            raise ProviderError(self.name, "SCHEMA_MISMATCH", 200)
        meta = data.get("meta", {})
        result = {
            "rows": rows,
            "reported_total": data.get("totalArticles", meta.get("found")),
            "has_more": meta.get("has_more"),
            "sample_size": len(rows),
        }
        if self.name == "freenews" and include_details:
            detailed = []
            for row in rows[:3]:  # bounded free quota usage; original_url only exists in /details
                if not row.get("uuid"):
                    continue
                detail = await self.http.json(
                    "https://api.freenewsapi.io/v1/details", params={"uuid": row["uuid"]}, headers=headers
                )
                article = detail.get("data")
                if isinstance(article, dict):
                    # Do not retain unlicensed article bodies or send them to AI.
                    detailed.append({k: v for k, v in article.items() if k != "body"})
            result["rows"] = detailed
            result["details_sample_size"] = len(detailed)
        return result

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
