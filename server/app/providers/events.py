from datetime import datetime
from urllib.parse import quote

from ..llm import DeterministicLLM
from ..models import Content, ContentType, DataMode, RightsStatus, Verification
from .base import (
    ProviderError,
    SafeHTTP,
    coordinates,
    end_of_day,
    parse_datetime,
    stable_id,
)
from .tour import TourEvents as TourEvents

SEOUL_EVENTS_DOC = "https://data.seoul.go.kr/dataList/OA-15486/A/1/datasetView.do"


class SeoulEvents:
    name = "seoul_events"

    def __init__(self, key="sample", timeout=10, transport=None):
        self.key = key
        self.http = SafeHTTP(self.name, timeout, transport)

    async def collect(self, now: datetime) -> tuple[list[Content], dict]:
        if not self.key:
            raise ProviderError(self.name, "MISSING_KEY")
        limit = 5 if self.key == "sample" else 100
        url = f"http://openapi.seoul.go.kr:8088/{quote(self.key, safe='')}/json/culturalEventInfo/1/{limit}/"
        data = await self.http.json(url)
        envelope = data.get("culturalEventInfo", data)
        code = envelope.get("RESULT", {}).get("CODE")
        if code != "INFO-000":
            raise ProviderError(self.name, code or "SCHEMA_MISMATCH", 200)
        rows = envelope.get("row", [])
        items = []
        for row in rows:
            end = end_of_day(row.get("END_DATE", ""))
            url = row.get("HMPG_ADDR") or row.get("ORG_LINK")
            if not end or not url:
                continue
            lat, lon = coordinates(row.get("LAT"), row.get("LOT"))
            category = row.get("CODENAME", "")
            tags = DeterministicLLM().classify(
                category + " " + row.get("TITLE", "") + " " + row.get("PROGRAM", "")
            )
            title = row.get("TITLE", "")
            try:
                items.append(
                    Content(
                        id=stable_id("seoul-event", url),
                        content_type=ContentType.EXHIBITION if "전시" in category else ContentType.EVENT,
                        title=title,
                        brief=f"서울시 문화행사 정보. {title}. 장소: {row.get('PLACE', '')}. "
                        f"일정: {row.get('DATE', '')}. 출처: 서울문화포털.",
                        source_name="서울특별시 서울문화포털",
                        source_url=url,
                        published_at=parse_datetime(row.get("RGSTDATE"), local=True),
                        updated_at=None,
                        starts_at=parse_datetime(row.get("STRTDATE"), local=True),
                        expires_at=end,
                        fetched_at=now,
                        latitude=lat,
                        longitude=lon,
                        interest_tags=tags,
                        rights_status=RightsStatus.TTS_ALLOWED,
                        rights_evidence_url=SEOUL_EVENTS_DOC,
                        verification_status=Verification.VERIFIED,
                        data_mode=DataMode.LIVE,
                        provenance="PUBLIC_API:seoul_culturalEventInfo;KOGL_TYPE1;classification=MOCK",
                        venue=row.get("PLACE"),
                    )
                )
            except ValueError:
                continue
        return items, {
            "raw_count": len(rows),
            "reported_total": envelope.get("list_total_count"),
            "sample": self.key == "sample",
            "source_updated_at_available": False,
        }
