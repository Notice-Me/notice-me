from datetime import datetime, timedelta

from .models import Content, ContentType, DataMode, RightsStatus, TrafficImpact, Verification

FIXTURE_LICENSE = (
    "https://github.com/Notice-Me/notice-me/blob/feat/server-content-feed/docs/FIXTURE_LICENSE.md"
)


def demo_contents(now: datetime) -> list[Content]:
    items = []
    definitions = [
        (
            "news-science",
            ContentType.NEWS,
            "[모의] 과학관 로봇 연구 소식",
            "과학IT",
            RightsStatus.TTS_ALLOWED,
        ),
        (
            "news-anime",
            ContentType.NEWS,
            "[모의] 새 애니메이션 제작 소식",
            "애니메이션",
            RightsStatus.LICENSE_UNVERIFIED,
        ),
        ("news-art", ContentType.NEWS, "[모의] 지역 공공미술 프로젝트", "예술", RightsStatus.LINK_ONLY),
        (
            "life-science",
            ContentType.LIFE,
            "[모의] 과학 프로그램 참가 안내",
            "과학IT",
            RightsStatus.TTS_ALLOWED,
        ),
        ("life-art", ContentType.LIFE, "[모의] 미술관 교육 안내", "예술", RightsStatus.TTS_ALLOWED),
        ("exhibition", ContentType.EXHIBITION, "[모의] 예술 전시", "예술", RightsStatus.TTS_ALLOWED),
        ("popup", ContentType.EVENT, "[모의] 캐릭터 팝업", "애니메이션", RightsStatus.TTS_ALLOWED),
    ]
    for slug, kind, title, tag, rights in definitions:
        event = kind in (ContentType.EVENT, ContentType.EXHIBITION)
        items.append(
            Content(
                id="mock:" + slug,
                content_type=kind,
                title=title,
                brief=f"{title}. 동작 검증용으로 작성된 가상의 콘텐츠입니다. 실제 소식이나 행사가 아닙니다.",
                source_name="Notice Me 자체 작성 모의 자료",
                source_url=f"https://example.invalid/notice-me/{slug}",
                published_at=now - timedelta(hours=1),
                updated_at=now - timedelta(minutes=5),
                fetched_at=now,
                expires_at=now + timedelta(days=1),
                latitude=37.57,
                longitude=126.98,
                interest_tags=[tag],
                rights_status=rights,
                rights_evidence_url=FIXTURE_LICENSE if rights == RightsStatus.TTS_ALLOWED else None,
                verification_status=Verification.SIMULATED,
                data_mode=DataMode.MOCK,
                provenance="SELF_AUTHORED_FIXTURE",
                venue="가상 행사장" if event else None,
                starts_at=now - timedelta(hours=1) if event else None,
            )
        )
    items.append(
        Content(
            id="mock:traffic",
            content_type=ContentType.TRAFFIC,
            title="[모의] 경로 차로 통제",
            brief="사고 우선순위 검증용 가상 차로 통제입니다. 실제 교통정보가 아닙니다.",
            source_name="Notice Me 자체 작성 모의 자료",
            source_url="https://example.invalid/notice-me/traffic",
            published_at=now - timedelta(minutes=2),
            updated_at=now,
            fetched_at=now,
            expires_at=now + timedelta(minutes=10),
            latitude=37.57,
            longitude=126.98,
            rights_status=RightsStatus.TTS_ALLOWED,
            rights_evidence_url=FIXTURE_LICENSE,
            verification_status=Verification.SIMULATED,
            priority=200,
            data_mode=DataMode.MOCK,
            provenance="SELF_AUTHORED_FIXTURE",
            traffic=TrafficImpact(
                occurred_at=now - timedelta(minutes=2),
                valid_until=now + timedelta(minutes=10),
                status="ACTIVE",
                affected_link_ids=["demo-link-1"],
                link_namespace="DEMO",
                extent_description="가상 링크 demo-link-1",
            ),
        )
    )
    return items
