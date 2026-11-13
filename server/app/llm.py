from typing import Protocol

from .interests import classify_categories
from .interests import normalize_interest as normalize_interest
from .models import Content, ExplainResponse
from .rights import tts_allowed


class LLMProvider(Protocol):
    mode: str

    def classify(self, text: str) -> list[str]: ...
    async def summarize(self, content: Content) -> str: ...
    async def explain(self, content: Content, question: str) -> ExplainResponse: ...


class DeterministicLLM:
    mode = "MOCK"

    def classify(self, text: str) -> list[str]:
        return classify_categories(text)

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
