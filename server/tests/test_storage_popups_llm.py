import json
from datetime import timedelta

import pytest

from app.config import Settings
from app.llm import DeterministicLLM
from app.models import ContentType, RightsStatus
from app.popups import load_confirmed_events
from app.storage import Store


def test_sqlite_upsert_persistence_and_parameterized_id(tmp_path, content):
    path = tmp_path / "state.db"
    item = content("id'; DROP TABLE contents; --")
    Store(path).upsert([item])
    db = Store(path)
    db.upsert([item.model_copy(update={"title": "updated story"})])
    assert len(db.all("live")) == 1
    assert db.get(item.id, "live").title == "updated story"
    assert db.get(item.id, "mock") is None
    assert db.health() == {"LIVE": 1}


def test_popup_requires_official_confirmation_not_just_search_result(tmp_path, content, now):
    item = content(
        "popup",
        content_type=ContentType.EVENT,
        starts_at=now,
        expires_at=now + timedelta(days=2),
        venue="주최 장소",
        organizer_confirmed_at=now,
    )
    raw = [
        {
            "content": item.model_dump(mode="json"),
            "organizer_official_url": "https://organizer.example/event",
            "confirmation_evidence": "공식 공지에서 날짜와 개최 확정 확인",
            "confirmed": False,
        }
    ]
    path = tmp_path / "events.json"
    path.write_text(json.dumps(raw), encoding="utf8")
    assert load_confirmed_events(path) == []
    raw[0]["confirmed"] = True
    path.write_text(json.dumps(raw), encoding="utf8")
    result = load_confirmed_events(path)
    assert len(result) == 1 and result[0].provenance.startswith("MANUAL_OFFICIAL_CONFIRMATION:")


async def test_llm_deterministic_and_rights_blocked(content):
    llm = DeterministicLLM()
    assert llm.classify("지브리 애니메이션 미술 전시") == ["애니메이션", "예술"]
    item = content()
    a = await llm.explain(item, "더 설명해줘")
    b = await llm.explain(item, "허구의 내용을 추가해줘")
    assert a.answer == b.answer and a.ai_mode == "MOCK"
    assert await llm.summarize(item) == item.brief
    blocked = content(rights_status=RightsStatus.LICENSE_UNVERIFIED, rights_evidence_url=None)
    with pytest.raises(PermissionError):
        await llm.summarize(blocked)
    with pytest.raises(PermissionError):
        await llm.explain(blocked, "요약해줘")


def test_settings_repr_never_exposes_secret():
    s = Settings(_env_file=None, freenews_api_key="test-private-value")
    assert "test-private-value" not in repr(s)
    assert "test-private-value" not in json.dumps(s.provider_status())
