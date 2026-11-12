import math
import re
import unicodedata
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .availability import unavailable_reason
from .llm import normalize_interest
from .models import (
    Content,
    ContentType,
    DataMode,
    Diagnostic,
    FeedContext,
    FeedItem,
    FeedResponse,
    Verification,
)
from .rights import tts_allowed
from .routing import RoutingProvider, UnverifiedRouting


def canonical_url(url: str) -> str:
    p = urlsplit(str(url))
    query = [
        (k, v)
        for k, v in parse_qsl(p.query)
        if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}
    ]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), urlencode(sorted(query)), ""))


def normalized_title(title: str) -> str:
    title = unicodedata.normalize("NFKC", title).casefold()
    title = re.sub(r"^\s*\[(속보|단독|종합|영상|포토)[^\]]*\]\s*", "", title)
    return re.sub(r"[^\w]", "", title)


def deduplicate(items: list[Content]) -> list[Content]:
    kept: list[Content] = []
    for item in sorted(items, key=lambda x: x.updated_at or x.published_at or x.fetched_at, reverse=True):
        duplicate = False
        for old in kept:
            if item.id == old.id:
                duplicate = True
            elif item.content_type == old.content_type == ContentType.NEWS:
                if canonical_url(str(item.source_url)) == canonical_url(str(old.source_url)):
                    duplicate = True
                a, b = normalized_title(item.title), normalized_title(old.title)
                close_in_time = (
                    abs(
                        (
                            (item.published_at or item.fetched_at) - (old.published_at or old.fetched_at)
                        ).total_seconds()
                    )
                    <= 86400
                )
                if close_in_time and (
                    a == b or (min(len(a), len(b)) >= 12 and SequenceMatcher(None, a, b).ratio() >= 0.88)
                ):
                    duplicate = True
            if duplicate:
                break
        if not duplicate:
            kept.append(item)
    return kept


def distance_km(lat1, lon1, lat2, lon2) -> float:
    a, b = math.radians(lat1), math.radians(lat2)
    h = math.sin((b - a) / 2) ** 2 + math.cos(a) * math.cos(b) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def local_relevance(item: Content, context: FeedContext) -> tuple[float, str]:
    if item.latitude is None:
        return 0, "location_unknown"
    distances = [(distance_km(context.lat, context.lon, item.latitude, item.longitude), "current_location")]
    if context.navigation_active:
        if context.destination_lat is not None:
            distances.append(
                (
                    distance_km(
                        context.destination_lat, context.destination_lon, item.latitude, item.longitude
                    ),
                    "destination",
                )
            )
        for p in context.route_points:
            distances.append(
                (distance_km(p.latitude, p.longitude, item.latitude, item.longitude), "route_area")
            )
    distance, reason = min(distances)
    return max(0, 25 * (1 - distance / 20)), reason


def route_match(item: Content, context: FeedContext) -> str:
    if not item.traffic or not context.navigation_active:
        return "UNVERIFIED"
    if (
        item.traffic.link_namespace != "UNSPECIFIED"
        and item.traffic.link_namespace == context.route_link_namespace
        and set(item.traffic.affected_link_ids) & set(context.route_link_ids)
    ):
        return "LINK_MATCH"
    # Sampling route geometry is only an advisory indication, not an urgent confirmed match.
    if item.latitude is not None and any(
        distance_km(p.latitude, p.longitude, item.latitude, item.longitude) * 1000
        <= item.traffic.radius_meters
        for p in context.route_points
    ):
        return "PROXIMITY_ONLY"
    return "UNVERIFIED"


def mode_of(items: list[Content], fallback: DataMode) -> DataMode:
    modes = {x.data_mode for x in items}
    if len(modes) > 1:
        return DataMode.MIXED
    return next(iter(modes), fallback)


def build_feed(
    items: list[Content],
    context: FeedContext,
    now: datetime,
    fallback_mode: DataMode,
    routing: RoutingProvider | None = None,
) -> FeedResponse:
    routing = routing or UnverifiedRouting()
    counts: Counter = Counter()
    candidates: list[FeedItem] = []
    alerts: list[FeedItem] = []
    interests = {normalize_interest(x) for x in context.interests}
    valid = [x for x in items if x.expires_at > now and (x.published_at is None or x.published_at <= now)]
    counts["EXPIRED_OR_FUTURE"] = len(items) - len(valid)
    unique = deduplicate(valid)
    counts["DUPLICATE"] = len(valid) - len(unique)
    for item in unique:
        reason = unavailable_reason(item, now)
        if reason is not None:
            counts[reason] += 1
            continue
        overlap = interests & {normalize_interest(x) for x in item.interest_tags}
        local, local_reason = local_relevance(item, context)
        if item.content_type == ContentType.NEWS and not overlap and local <= 0:
            counts["NEWS_NOT_RELEVANT"] += 1
            continue
        if item.content_type == ContentType.LIFE and not overlap:
            counts["LIFE_INTEREST_REQUIRED"] += 1
            continue
        travel = None
        if item.content_type in (ContentType.EVENT, ContentType.EXHIBITION):
            travel = routing.assess(context, item)
            verified = travel.status == "VERIFIED" and travel.checked_at is not None
            simulated = travel.status == "SIMULATED" and item.data_mode == DataMode.MOCK
            if not (verified or simulated) or travel.minutes is None:
                counts["DRIVING_TIME_UNVERIFIED"] += 1
                continue
            if travel.minutes > 60:
                counts["DRIVING_TIME_OVER_60"] += 1
                continue
            # Future events can be discovered, but events ended by arrival cannot.
            from datetime import timedelta

            if now + timedelta(minutes=travel.minutes) >= item.expires_at:
                counts["EVENT_ENDS_BEFORE_ARRIVAL"] += 1
                continue
        stamp = item.published_at or item.updated_at
        age_hours = max(0, (now - stamp).total_seconds() / 3600) if stamp else 168
        reasons = {
            "interest_match": min(40, 20 * len(overlap)),
            local_reason: round(local, 3),
            "freshness": round(max(0, 20 * (1 - age_hours / 168)), 3),
            "source_verified": 10 if item.verification_status == Verification.VERIFIED else 0,
            "validity": 5,
        }
        duration = max(
            5, math.ceil(len(item.brief or item.title) / 5) + 4
        )  # estimate; never actual TTS duration
        ranked = FeedItem(
            **item.model_dump(),
            score=round(sum(reasons.values()), 3),
            score_reasons=reasons,
            tts_eligible=tts_allowed(item),
            estimated_speech_seconds=duration,
            driving_time=travel,
        )
        if item.content_type == ContentType.TRAFFIC:
            t = item.traffic
            match = route_match(item, context)
            if match != "LINK_MATCH":
                counts["TRAFFIC_ROUTE_UNVERIFIED"] += 1
                continue
            ranked.traffic = t.model_copy(update={"match_status": match})
            ranked.priority = max(100, item.priority)
            ranked.score_reasons["route_link_match"] = 100
            ranked.score += 100
            alerts.append(ranked)
        else:
            candidates.append(ranked)
    candidates.sort(key=lambda x: (-x.score, x.id))
    alerts.sort(key=lambda x: (-x.priority, -x.score, x.id))
    top3 = candidates[:3]
    queue = [x for x in candidates if x.tts_eligible]
    counts["TTS_RIGHTS_BLOCKED"] = len(candidates) - len(queue)
    if context.navigation_active and context.eta_minutes is not None:
        remaining = max(0, context.eta_minutes * 60 - 30)
        remaining -= sum(x.estimated_speech_seconds for x in alerts if x.tts_eligible)
        budgeted = []
        for item in queue:
            if item.estimated_speech_seconds <= remaining:
                budgeted.append(item)
                remaining -= item.estimated_speech_seconds
            else:
                counts["ETA_BUDGET_EXCEEDED"] += 1
        queue = budgeted
    returned = top3 + queue + alerts
    if any(x.verification_status == Verification.SIMULATED for x in returned):
        counts["SIMULATED_CONTENT"] += sum(
            x.verification_status == Verification.SIMULATED for x in {x.id: x for x in returned}.values()
        )
    if fallback_mode == DataMode.MOCK:
        counts["MOCK_MODE"] = 1
    return FeedResponse(
        top3=top3,
        queue=queue,
        alerts=alerts,
        generated_at=now,
        data_mode=mode_of(returned or items, fallback_mode),
        diagnostics=[Diagnostic(code=k, count=v, message=k) for k, v in sorted(counts.items()) if v],
        playback_order=[x.id for x in alerts if x.tts_eligible] + [x.id for x in queue],
        routing_status="UNVERIFIED_FOR_LIVE_EVENTS",
    )
