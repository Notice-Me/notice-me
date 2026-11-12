from datetime import datetime

from .models import Content, ContentType, Verification


def unavailable_reason(item: Content, now: datetime) -> str | None:
    """Content validity shared by feed, detail and explain; rights are checked separately.

    This does not establish route relevance or driving time. A valid detail response
    is never permission to bypass the feed's route/interest/routing filters.
    """
    if item.expires_at <= now or (item.published_at is not None and item.published_at > now):
        return "EXPIRED_OR_FUTURE"
    if item.verification_status == Verification.UNVERIFIED:
        return "UNVERIFIED_CONTENT"
    if item.content_type == ContentType.TRAFFIC:
        impact = item.traffic
        if (
            impact is None
            or impact.status != "ACTIVE"
            or not (impact.occurred_at <= now < impact.valid_until)
        ):
            return "TRAFFIC_INVALID"
        if (now - item.fetched_at).total_seconds() > 600:
            return "TRAFFIC_STALE"
    return None
