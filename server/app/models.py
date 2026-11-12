from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator


def utcnow() -> datetime:
    return datetime.now(UTC)


class DataMode(StrEnum):
    LIVE = "LIVE"
    MOCK = "MOCK"
    MIXED = "MIXED"


class RightsStatus(StrEnum):
    TTS_ALLOWED = "TTS_ALLOWED"
    LINK_ONLY = "LINK_ONLY"
    LICENSE_UNVERIFIED = "LICENSE_UNVERIFIED"


class Verification(StrEnum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    SIMULATED = "SIMULATED"


class ContentType(StrEnum):
    NEWS = "NEWS"
    EVENT = "EVENT"
    EXHIBITION = "EXHIBITION"
    LIFE = "LIFE"
    TRAFFIC = "TRAFFIC"


class Point(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class TrafficImpact(BaseModel):
    occurred_at: AwareDatetime
    valid_until: AwareDatetime
    status: str
    affected_link_ids: list[str] = Field(default_factory=list)
    link_namespace: str = "UNSPECIFIED"
    radius_meters: float = Field(default=200, gt=0, le=5000)
    extent_description: str
    native_x: float | None = None
    native_y: float | None = None
    native_crs: str | None = None
    # Coordinate proximity is an advisory candidate, never proof of road/direction impact.
    match_status: str = "UNVERIFIED"


class WeatherObservation(BaseModel):
    """Named observation area; never inferred from the requesting vehicle's location."""

    area_code: Literal["POI009"]
    region: str = Field(min_length=1, max_length=200)
    observed_at: AwareDatetime
    scope: Literal["FIXED_OBSERVATION_AREA"] = "FIXED_OBSERVATION_AREA"


class Content(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=180)
    content_type: ContentType
    title: str = Field(min_length=1, max_length=1000)
    brief: str = Field(default="", max_length=4000)
    source_name: str
    source_url: HttpUrl
    published_at: AwareDatetime | None = None
    updated_at: AwareDatetime | None = None
    expires_at: AwareDatetime
    fetched_at: AwareDatetime
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    interest_tags: list[str] = Field(default_factory=list)
    rights_status: RightsStatus = RightsStatus.LICENSE_UNVERIFIED
    rights_evidence_url: HttpUrl | None = None
    verification_status: Verification = Verification.UNVERIFIED
    priority: int = Field(default=0, ge=0, le=1000)
    data_mode: DataMode
    provenance: str
    starts_at: AwareDatetime | None = None
    venue: str | None = None
    organizer_confirmed_at: AwareDatetime | None = None
    traffic: TrafficImpact | None = None
    weather: WeatherObservation | None = None

    @model_validator(mode="after")
    def validate_provenance(self):
        if self.data_mode == DataMode.MIXED:
            raise ValueError("An individual content item must be LIVE or MOCK")
        if self.verification_status == Verification.SIMULATED and self.data_mode != DataMode.MOCK:
            raise ValueError("SIMULATED content must be MOCK")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Coordinates must be provided as a pair")
        if self.rights_status == RightsStatus.TTS_ALLOWED and not self.rights_evidence_url:
            raise ValueError("TTS_ALLOWED requires license evidence")
        if self.weather is not None and self.content_type != ContentType.LIFE:
            raise ValueError("Weather observations must be LIFE content")
        return self


class ContentDetail(Content):
    is_expired: bool
    tts_eligible: bool


class CollectionStatus(BaseModel):
    collected_at: AwareDatetime
    provider: str
    status: str
    item_count: int = Field(ge=0)
    code: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["ok"]
    configured_data_mode: DataMode
    stored_counts: dict[str, int]
    providers: dict[str, bool | str]
    collections: list[CollectionStatus]


class FeedContext(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    interests: list[str] = Field(default_factory=list, max_length=30)
    navigation_active: bool = False
    destination_lat: float | None = Field(default=None, ge=-90, le=90)
    destination_lon: float | None = Field(default=None, ge=-180, le=180)
    eta_minutes: float | None = Field(default=None, ge=0, le=1440)
    route_points: list[Point] = Field(default_factory=list, max_length=500)
    route_link_ids: list[str] = Field(default_factory=list, max_length=1000)
    route_link_namespace: str = "UNSPECIFIED"

    @model_validator(mode="after")
    def validate_navigation(self):
        if (self.destination_lat is None) != (self.destination_lon is None):
            raise ValueError("destination_lat and destination_lon must be provided together")
        if not self.navigation_active and (
            self.destination_lat is not None
            or self.eta_minutes is not None
            or self.route_points
            or self.route_link_ids
        ):
            raise ValueError("Navigation fields require navigation_active=true")
        return self


class TravelAssessment(BaseModel):
    status: str = "UNVERIFIED"
    minutes: float | None = Field(default=None, ge=0)
    provider: str = "none"
    checked_at: AwareDatetime | None = None


class FeedItem(Content):
    score: float = 0
    score_reasons: dict[str, float] = Field(default_factory=dict)
    tts_eligible: bool = False
    estimated_speech_seconds: int = 0
    driving_time: TravelAssessment | None = None


class Diagnostic(BaseModel):
    code: str
    count: int = 1
    message: str


class FeedResponse(BaseModel):
    top3: list[FeedItem] = Field(max_length=3)
    queue: list[FeedItem]
    alerts: list[FeedItem]
    generated_at: AwareDatetime
    data_mode: DataMode
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    playback_order: list[str] = Field(default_factory=list)
    routing_status: str = "UNVERIFIED"


class ExplainRequest(BaseModel):
    question: str = Field(default="자세히 알려줘", min_length=1, max_length=500)


class ExplainResponse(BaseModel):
    content_id: str
    answer: str
    ai_mode: str
    provider: str
    source_urls: list[HttpUrl]
    grounding: str
