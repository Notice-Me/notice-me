"""Manual organizer-confirmed popups; no crawler or unaudited auto-discovery."""

import json
from pathlib import Path

from pydantic import BaseModel, HttpUrl

from .models import Content, ContentType, DataMode, Verification


class ManualEvent(BaseModel):
    content: Content
    organizer_official_url: HttpUrl
    confirmation_evidence: str
    confirmed: bool


def load_confirmed_events(path: Path) -> list[Content]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    accepted = []
    for record in raw:
        event = ManualEvent.model_validate(record)
        c = event.content
        if (
            event.confirmed
            and event.confirmation_evidence.strip()
            and c.organizer_confirmed_at
            and c.starts_at
            and c.venue
            and c.latitude is not None
            and c.expires_at > c.starts_at
            and c.verification_status == Verification.VERIFIED
            and c.data_mode == DataMode.LIVE
            and c.content_type in (ContentType.EVENT, ContentType.EXHIBITION)
        ):
            # The manual reviewer attests the URL belongs to the organizer; no automatic trust of arbitrary URL.
            accepted.append(
                c.model_copy(
                    update={"provenance": "MANUAL_OFFICIAL_CONFIRMATION:" + str(event.organizer_official_url)}
                )
            )
    return accepted
