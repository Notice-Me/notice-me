from datetime import UTC, datetime

import pytest

from app.fixtures import demo_contents
from app.models import ContentType, DataMode, FeedContext, Verification


@pytest.fixture
def now():
    return datetime(2026, 11, 11, 0, 0, tzinfo=UTC)


@pytest.fixture
def content(now):
    def make(slug="test", **updates):
        item = demo_contents(now)[0]
        changes = dict(
            id=slug,
            title="A distinct science story " + slug,
            source_url=f"https://example.org/articles/{slug}",
            content_type=ContentType.NEWS,
            data_mode=DataMode.LIVE,
            verification_status=Verification.VERIFIED,
        )
        changes.update(updates)
        # Validate modified fixtures to catch invalid public API contracts.
        return type(item).model_validate({**item.model_dump(), **changes})

    return make


@pytest.fixture
def context():
    return FeedContext(lat=37.57, lon=126.98, interests=["과학IT", "예술", "애니메이션"])
