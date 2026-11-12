from typing import Protocol

from .models import Content, ExplainResponse
from .rights import tts_allowed

TAG_KEYWORDS = {
    "애니메이션": ("애니메이션", "지브리", "치이카와", "캐릭터", "animation", "anime"),
    "과학IT": ("과학", "it", "인공지능", "기술", "science", "technology", "ai"),
    "예술": ("예술", "미술", "전시", "공연", "연극", "클래식", "콘서트", "art", "museum"),
    "생활": ("날씨", "기온", "생활", "weather"),
}


def normalize_interest(tag: str) -> str:
    value = tag.strip().casefold().replace("/", "").replace(" ", "")
    aliases = {
        "과학it": "과학IT",
        "과학": "과학IT",
        "it": "과학IT",
        "science": "과학IT",
        "animation": "애니메이션",
        "anime": "애니메이션",
        "art": "예술",
        "weather": "생활",
        "날씨": "생활",
        "기온": "생활",
    }
    return aliases.get(value, tag.strip())


class LLMProvider(Protocol):
    mode: str

    def classify(self, text: str) -> list[str]: ...
    async def summarize(self, content: Content) -> str: ...
    async def explain(self, content: Content, question: str) -> ExplainResponse: ...


class DeterministicLLM:
    mode = "MOCK"

    def classify(self, text: str) -> list[str]:
        value = text.casefold()
        return [tag for tag, words in TAG_KEYWORDS.items() if any(w in value for w in words)]

    async def summarize(self, content: Content) -> str:
        if not tts_allowed(content):
            raise PermissionError("RIGHTS_NOT_CLEARED")
        return content.brief or content.title

    async def explain(self, content: Content, question: str) -> ExplainResponse:
        if not tts_allowed(content):
            raise PermissionError("RIGHTS_NOT_CLEARED")
        # No generative model or remote endpoint. Arbitrary questions do not add facts.
        facts = [content.title, content.brief]
        if content.venue:
            facts.append(f"장소: {content.venue}")
        if content.starts_at:
            facts.append(f"시작: {content.starts_at.isoformat()}")
        facts.append(f"정보 유효기한: {content.expires_at.isoformat()}")
        return ExplainResponse(
            content_id=content.id,
            answer="\n".join(x for x in facts if x),
            ai_mode="MOCK",
            provider="deterministic",
            source_urls=[content.source_url],
            grounding="STORED_FIELDS_ONLY; 질문에 대한 추가 사실은 생성하지 않음",
        )
