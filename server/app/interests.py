"""Deterministic matching of public metadata. No LLM, article body or user history."""

import re
import unicodedata
from dataclasses import dataclass

from .models import Content, ContentType

CATEGORIES = {
    "애니메이션": ("애니메이션", "animation", "anime", "アニメ", "アニメーション"),
    "과학IT": ("과학IT", "과학/IT", "과학", "it", "science", "technology", "ai"),
    "예술": ("예술", "art", "미술", "museum"),
    "생활": ("생활", "weather", "날씨", "기온"),
}
CATEGORY_SIGNALS = {
    "애니메이션": ("애니메이션", "지브리", "캐릭터", "animation", "anime", "アニメ"),
    "과학IT": ("과학", "인공지능", "기술", "science", "technology", "IT", "AI"),
    "예술": ("예술", "미술", "전시", "공연", "연극", "클래식", "콘서트", "art", "museum"),
    "생활": ("생활", "날씨", "기온", "weather"),
}
TOPICS = {"chiikawa": ("먼작귀", "치이카와", "Chiikawa", "ちいかわ")}
FORMATS = {
    "popup": (
        "팝업스토어",
        "팝업 스토어",
        "팝업",
        "popup",
        "pop-up",
        "pop up",
        "popup store",
        "pop-up store",
        "pop up store",
        "ポップアップ",
        "ポップアップストア",
    ),
    "character_goods": ("캐릭터 굿즈", "캐릭터굿즈", "character goods", "キャラクターグッズ"),
    "exhibition": ("전시회", "전시", "exhibition", "展覧会", "展示会"),
}


def normalized(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().strip()


def alias_key(value: str) -> str:
    return re.sub(r"[\s/_-]+", "", normalized(value))


def phrase_in(text: str, phrase: str) -> bool:
    """ASCII words need boundaries; CJK phrases may carry grammatical suffixes."""
    text, phrase = normalized(text), normalized(phrase)
    pattern = r"\s*".join(re.escape(part) for part in phrase.split())
    if re.search(r"[a-z0-9]", phrase):
        pattern = r"(?<![a-z0-9])" + pattern + r"(?![a-z0-9])"
    return bool(phrase and re.search(pattern, text))


def aliases_in(text: str, catalog: dict[str, tuple[str, ...]]) -> frozenset[str]:
    return frozenset(key for key, aliases in catalog.items() if any(phrase_in(text, a) for a in aliases))


def classify_categories(text: str) -> list[str]:
    result = []
    raw = unicodedata.normalize("NFKC", text)
    for category, signals in CATEGORY_SIGNALS.items():
        if any(
            bool(re.search(r"(?<![A-Za-z0-9])" + s + r"(?![A-Za-z0-9])", raw))
            if s in {"IT", "AI"}
            else phrase_in(text, s)
            for s in signals
        ) or (category == "애니메이션" and aliases_in(text, TOPICS)):
            result.append(category)
    return result


def normalize_interest(tag: str) -> str:
    return next(
        (
            category
            for category, aliases in CATEGORIES.items()
            if alias_key(tag) in {alias_key(a) for a in aliases}
        ),
        tag.strip(),
    )


@dataclass(frozen=True)
class InterestProfile:
    categories: frozenset[str]
    topics: frozenset[str]
    formats: frozenset[str]
    keywords: tuple[str, ...]
    unsupported: tuple[str, ...]

    @property
    def specific(self) -> bool:
        return bool(self.topics or self.formats or self.keywords or self.unsupported)


def parse_interests(values: list[str]) -> InterestProfile:
    groups: list[set[str]] = [set(), set(), set()]
    keywords, unsupported = set(), set()
    for value in values:
        key = alias_key(value)
        if not key:
            continue
        found = False
        for group, catalog in zip(groups, (CATEGORIES, TOPICS, FORMATS), strict=True):
            for canonical, aliases in catalog.items():
                if key in {alias_key(a) for a in aliases}:
                    group.add(canonical)
                    found = True
        if not found:
            term = normalized(value)
            (keywords if 2 <= len(term) <= 120 and any(c.isalnum() for c in term) else unsupported).add(term)
    return InterestProfile(
        *(frozenset(group) for group in groups), tuple(sorted(keywords)), tuple(sorted(unsupported))
    )


def title_formats(item: Content, topics: frozenset[str]) -> frozenset[str]:
    title = item.title
    result = set(aliases_in(title, {"exhibition": FORMATS["exhibition"]}))
    if item.content_type == ContentType.EXHIBITION:
        result.add("exhibition")
    goods = any(phrase_in(title, a) for a in ("굿즈", "goods", "グッズ"))
    character = bool(topics) or any(
        phrase_in(title, a) for a in ("캐릭터", "character", "キャラクター", "애니메이션", "anime")
    )
    if goods and character:
        result.add("character_goods")
    full_store = any(
        phrase_in(title, a)
        for a in (
            "팝업스토어",
            "팝업 스토어",
            "popup store",
            "pop-up store",
            "pop up store",
            "ポップアップストア",
        )
    )
    bare_popup = bool(aliases_in(title, {"popup": FORMATS["popup"]}))
    browser = any(phrase_in(title, a) for a in ("브라우저", "팝업 차단", "popup blocker", "pop-up blocker"))
    store_context = (
        character
        or item.content_type in (ContentType.EVENT, ContentType.EXHIBITION)
        or any(phrase_in(title, a) for a in ("매장", "스토어", "백화점", "shop", "store"))
    )
    if full_store or (bare_popup and store_context and not browser):
        result.add("popup")
    return frozenset(result)


@dataclass(frozen=True)
class InterestMatch:
    matched: bool
    categories: frozenset[str]
    topics: frozenset[str]
    formats: frozenset[str]
    keyword_count: int

    def scores(self) -> dict[str, float]:
        return {
            "interest_match": min(40, 20 * len(self.categories)),
            "interest_topic": 30 if self.topics else 0,
            "interest_keyword": min(50, 25 * self.keyword_count),
            "interest_format": min(20, 10 * len(self.formats)),
        }


def match_interests(item: Content, profile: InterestProfile) -> InterestMatch:
    categories = profile.categories & {normalize_interest(tag) for tag in item.interest_tags}
    if profile.specific:
        # Legacy provider tags may contain the old collection search term.
        categories = profile.categories & set(classify_categories(item.title))
    topics = profile.topics & aliases_in(item.title, TOPICS)
    formats = profile.formats & title_formats(item, aliases_in(item.title, TOPICS))
    keywords = sum(phrase_in(item.title, word) for word in profile.keywords)
    matched = bool(categories)
    if profile.specific:
        anchor = (
            bool(topics or keywords)
            if profile.topics or profile.keywords
            else bool(categories)
            if profile.categories
            else bool(formats)
        )
        matched = anchor and (not profile.formats or bool(formats))
    # Explicit weather remains independent of a user's character/news preferences.
    if item.weather is not None and "생활" in profile.categories:
        matched = True
    return InterestMatch(matched, frozenset(categories), frozenset(topics), frozenset(formats), keywords)
