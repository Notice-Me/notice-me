"""Bounded TourAPI festival collection with per-row, credential-free decisions."""

import re
from collections import Counter
from datetime import datetime, timedelta

from pydantic import ValidationError

from ..llm import DeterministicLLM
from ..models import Content, ContentType, DataMode, RightsStatus, Verification
from .base import (
    KST,
    ProviderError,
    RequestBudget,
    SafeHTTP,
    coordinates,
    end_of_day,
    parse_datetime,
    stable_id,
)

TOUR_DOC = "https://www.data.go.kr/data/15101578/openapi.do"
TOUR_URL = "https://apis.data.go.kr/B551011/KorService2/searchFestival2"
# Official manual v4.4 uses '선택안함'; Swagger names cancellation and postponement.
NORMAL_PROGRESS = {"", "선택안함"}
BLOCKED_PROGRESS = {"취소": "CANCELLED", "행사연기": "POSTPONED"}


def event_date(value):
    value = str(value or "").strip()
    if not re.fullmatch(r"\d{8}", value):
        return None
    return parse_datetime(value, local=True)


class TourEvents:
    name = "tourapi"

    def __init__(
        self,
        key: str,
        timeout=10,
        transport=None,
        *,
        page_size=50,
        max_pages=3,
        lookahead_days=90,
        request_budget=3,
    ):
        if not (
            1 <= page_size <= 100
            and 1 <= max_pages <= 10
            and 1 <= lookahead_days <= 180
            and 1 <= request_budget <= 10
        ):
            raise ValueError("Invalid TourAPI collection limits")
        self.key = key
        self.page_size, self.max_pages, self.lookahead_days = page_size, max_pages, lookahead_days
        self.http = SafeHTTP(
            self.name,
            timeout,
            transport,
            min_interval=1,
            budget=RequestBudget(request_budget),
            total_timeout=30,
        )

    async def fetch_page(self, params):
        response = await self.http.get(TOUR_URL, params={**params, "serviceKey": self.key})
        try:
            data = response.json()["response"]
        except (ValueError, KeyError, TypeError):
            # The gateway can report authentication/quotas as XML, even with HTTP200.
            from defusedxml import ElementTree

            try:
                root = ElementTree.fromstring(response.content)
                code = root.findtext(".//returnReasonCode") or root.findtext(".//resultCode")
            except Exception:
                code = None
            raise ProviderError(
                self.name,
                "RATE_LIMITED"
                if code in {"22", "23"}
                else "AUTH_OR_GATEWAY_ERROR"
                if code
                else "SCHEMA_MISMATCH",
                response.status_code,
            ) from None
        if not isinstance(data, dict) or not isinstance(data.get("header"), dict):
            raise ProviderError(self.name, "SCHEMA_MISMATCH", response.status_code)
        code = str(data["header"].get("resultCode"))
        if code != "0000":
            raise ProviderError(self.name, "RATE_LIMITED" if code in {"22", "23"} else "PROVIDER_ERROR", 200)
        body = data.get("body")
        if not isinstance(body, dict):
            raise ProviderError(self.name, "SCHEMA_MISMATCH", 200)
        raw = body.get("items")
        if raw in (None, ""):
            rows = []
        elif isinstance(raw, dict):
            rows = raw.get("item", [])
            if rows in (None, ""):
                rows = []
            if isinstance(rows, dict):
                rows = [rows]
        else:
            raise ProviderError(self.name, "SCHEMA_MISMATCH", 200)
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ProviderError(self.name, "SCHEMA_MISMATCH", 200)
        try:
            total = int(body["totalCount"]) if body.get("totalCount") is not None else None
            size = int(body.get("numOfRows", self.page_size))
            page = int(body.get("pageNo", params["pageNo"]))
            if (
                size < 0
                or (size == 0 and rows)
                or (total is not None and total < 0)
                or page != params["pageNo"]
            ):
                raise ValueError()
        except (TypeError, ValueError):
            raise ProviderError(self.name, "SCHEMA_MISMATCH", 200) from None
        return rows, total, size

    def normalize(self, rows, now):
        today = now.astimezone(KST).date()
        horizon = today + timedelta(days=self.lookahead_days)
        items, decisions = [], []
        for row in rows:
            content_id = str(row.get("contentid") or "").strip()
            raw_progress = row.get("progresstype")
            progress = "" if raw_progress is None else str(raw_progress).strip()
            start, last_day = event_date(row.get("eventstartdate")), event_date(row.get("eventenddate"))
            end = end_of_day(str(row["eventenddate"])) if last_day else None
            reasons, warnings = [], []
            if not content_id:
                reasons.append("MISSING_CONTENT_ID")
            if progress in BLOCKED_PROGRESS:
                reasons.append(BLOCKED_PROGRESS[progress])
            elif progress not in NORMAL_PROGRESS:
                reasons.append("UNKNOWN_PROGRESS_TYPE")
            if not start:
                reasons.append("INVALID_START_DATE")
            if not end:
                reasons.append("INVALID_END_DATE")
            if start and last_day and last_day < start:
                reasons.append("END_BEFORE_START")
            if end and end <= now:
                reasons.append("EXPIRED_EVENT")
            if start and start.astimezone(KST).date() > horizon:
                reasons.append("OUTSIDE_HORIZON")
            decision = {
                "contentid": content_id,
                "eventstartdate": row.get("eventstartdate"),
                "eventenddate": row.get("eventenddate"),
                "progresstype": progress,
                "cpyrhtDivCd": row.get("cpyrhtDivCd"),
                "reasons": reasons,
                "warnings": warnings,
                "normalized": False,
            }
            if not reasons:
                lat, lon = coordinates(row.get("mapy"), row.get("mapx"))
                if lat is None:
                    warnings.append("COORDINATES_UNAVAILABLE")
                rights = row.get("cpyrhtDivCd") == "Type1"
                if not rights:
                    warnings.append("RIGHTS_UNVERIFIED")
                title = row.get("title", "")
                if not isinstance(title, str):
                    reasons.append("INVALID_CONTENT_FIELDS")
                    decision["invalidate_previous"] = True
                    decisions.append(decision)
                    continue
                try:
                    item = Content(
                        id=stable_id("tour-event", content_id),
                        content_type=ContentType.EVENT,
                        title=title,
                        brief=(
                            f"한국관광공사 행사정보. {title}. 장소: {row.get('addr1', '')}. "
                            f"일정: {row.get('eventstartdate', '')}~{row.get('eventenddate', '')}."
                            if rights
                            else ""
                        ),
                        source_name="한국관광공사 TourAPI",
                        source_url=TOUR_DOC,
                        published_at=parse_datetime(row.get("createdtime"), local=True),
                        updated_at=parse_datetime(row.get("modifiedtime"), local=True),
                        starts_at=start,
                        expires_at=end,
                        fetched_at=now,
                        latitude=lat,
                        longitude=lon,
                        interest_tags=DeterministicLLM().classify(title),
                        rights_status=RightsStatus.TTS_ALLOWED if rights else RightsStatus.LICENSE_UNVERIFIED,
                        rights_evidence_url=TOUR_DOC if rights else None,
                        verification_status=Verification.VERIFIED,
                        data_mode=DataMode.LIVE,
                        provenance="PUBLIC_API:tourapi_searchFestival2;classification=MOCK",
                        venue=row.get("addr1"),
                    )
                except (ValidationError, TypeError):
                    reasons.append("INVALID_CONTENT_FIELDS")
                else:
                    items.append(item)
                    decision.update(
                        normalized=True,
                        date_status="ONGOING" if start.astimezone(KST).date() <= today else "UPCOMING",
                    )
            decision["invalidate_previous"] = bool(reasons and any(r != "OUTSIDE_HORIZON" for r in reasons))
            decisions.append(decision)
        return items, decisions

    async def collect(self, now: datetime, *, probe=False, checkpoint=None) -> tuple[list[Content], dict]:
        if not self.key and not probe:
            raise ProviderError(self.name, "MISSING_KEY")
        today = now.astimezone(KST).date()
        query = {
            "MobileOS": "ETC",
            "MobileApp": "NoticeMe",
            "_type": "json",
            "arrange": "C",
            "eventStartDate": today.strftime("%Y%m%d"),
            "eventEndDate": (today + timedelta(days=self.lookahead_days)).strftime("%Y%m%d"),
            "numOfRows": self.page_size,
        }
        items, pages, decisions, seen, invalidated = {}, [], [], set(), set()
        stop, totals, received = "PAGE_LIMIT", [], 0
        for page_no in range(1, self.max_pages + 1):
            try:
                rows, total, size = await self.fetch_page({**query, "pageNo": page_no})
            except ProviderError as error:
                if not pages:
                    raise
                stop = error.code
                pages.append(
                    {
                        "page_no": page_no,
                        "status": "FAILED",
                        "code": error.code,
                        "http_status": error.http_status,
                        "timeout_phase": error.timeout_phase,
                    }
                )
                break
            totals.append(total)
            page_items, outcomes = self.normalize(rows, now)
            for item in page_items:
                items.setdefault(item.id, item)
            for outcome in outcomes:
                identity = outcome["contentid"]
                if identity and identity in seen:
                    outcome["warnings"].append("DUPLICATE_CONTENT_ID")
                if identity:
                    seen.add(identity)
                if identity and outcome["invalidate_previous"]:
                    invalidated.add(stable_id("tour-event", identity))
            for identity in invalidated:
                items.pop(identity, None)
            page_items = [x for x in page_items if x.id not in invalidated]
            page = {
                "page_no": page_no,
                "status": "SUCCESS",
                "http_status": self.http.last_http_status,
                "raw_count": len(rows),
                "reported_total": total,
                "response_page_size": size,
                "query": {**query, "pageNo": page_no},
                "observed_at": now.isoformat(),
                "rows": outcomes,
            }
            # The CLI persists this page before attempting another request.
            if checkpoint:
                checkpoint(page_items, page)
            pages.append(page)
            decisions.extend(outcomes)
            received += len(rows)
            if not rows:
                stop = (
                    "EMPTY_PAGE_BEFORE_TOTAL" if total is not None and received < total else "END_OF_RESULTS"
                )
                break
            # Actual TourAPI last-page numOfRows may be the returned count (27), not stride (50).
            if total is not None and received >= total:
                stop = "END_OF_RESULTS"
                break
        changed = len(set(totals)) > 1
        duplicates = sum("DUPLICATE_CONTENT_ID" in x["warnings"] for x in decisions)
        complete = stop == "END_OF_RESULTS" and not changed and not duplicates
        ordered = sorted(
            items.values(), key=lambda x: (x.starts_at.astimezone(KST).date() > today, x.starts_at, x.id)
        )
        return ordered, {
            "raw_count": sum(p.get("raw_count", 0) for p in pages),
            "reported_total": totals[0] if totals else None,
            "normalized_count": len(ordered),
            "excluded_count": sum(not x["normalized"] for x in decisions),
            "normalized_row_count": sum(x["normalized"] for x in decisions),
            "duplicate_row_count": duplicates,
            "excluded_by_reason": dict(Counter(r for x in decisions for r in x["reasons"])),
            "ongoing_count": sum(x.starts_at.astimezone(KST).date() <= today for x in ordered),
            "upcoming_count": sum(x.starts_at.astimezone(KST).date() > today for x in ordered),
            "requests_made": self.http.calls,
            "request_budget": self.http.budget.limit,
            "coverage_complete": complete,
            "collection_status": "SUCCESS" if complete else "PARTIAL",
            "stop_reason": stop,
            "totals_changed_during_collection": changed,
            "pages": pages,
            "date_timezone": "Asia/Seoul",
            "overlap_check": "start <= horizon and end >= today",
            "progress_policy": "empty/manual-default accepted; cancel/postpone/unknown excluded",
            "source_updated_at_is_fetch_time": False,
        }
