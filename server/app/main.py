import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import ValidationError

from .availability import unavailable_reason
from .config import Settings
from .fixtures import demo_contents
from .llm import DeterministicLLM
from .models import (
    ContentDetail,
    DataMode,
    ExplainRequest,
    ExplainResponse,
    FeedContext,
    FeedResponse,
    HealthResponse,
    Point,
    utcnow,
)
from .recommendation import build_feed
from .rights import tts_allowed, voice_allowed
from .routing import DemoRouting, RoutingProvider, UnverifiedRouting
from .storage import Store

# httpx INFO logs include full URLs, which may contain credentials.
logging.getLogger("httpx").setLevel(logging.WARNING)


def create_app(
    settings: Settings | None = None, routing: RoutingProvider | None = None, seed_demo=True
) -> FastAPI:
    settings = settings or Settings()
    store = Store(settings.db_path)

    @asynccontextmanager
    async def lifespan(app):
        if seed_demo and settings.data_mode in ("mock", "mixed"):
            store.upsert(demo_contents(utcnow()))
        yield

    app = FastAPI(title="Notice Me Content Server", version="0.1.0", lifespan=lifespan)
    app.state.store = store
    app.state.settings = settings
    llm = DeterministicLLM()
    routing = routing or (DemoRouting() if settings.data_mode in ("mock", "mixed") else UnverifiedRouting())

    @app.get("/api/v1/health", response_model=HealthResponse)
    def health():
        return {
            "status": "ok",
            "database": "ok",
            "configured_data_mode": settings.data_mode.upper(),
            "stored_counts": store.health(),
            "providers": settings.provider_status(),
            "collections": store.recent_collections(),
        }

    @app.get("/api/v1/feed", response_model=FeedResponse)
    def feed(
        lat: Annotated[float, Query(ge=-90, le=90)],
        lon: Annotated[float, Query(ge=-180, le=180)],
        interests: Annotated[list[str] | None, Query(max_length=30)] = None,
        navigation_active: bool = False,
        destination_lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
        destination_lon: Annotated[float | None, Query(ge=-180, le=180)] = None,
        eta_minutes: Annotated[float | None, Query(ge=0, le=1440)] = None,
        route_points: Annotated[list[str] | None, Query(max_length=500)] = None,
        route_link_ids: Annotated[list[str] | None, Query(max_length=1000)] = None,
        route_link_namespace: str = "UNSPECIFIED",
    ):
        try:
            tags = [tag.strip() for value in (interests or []) for tag in value.split(",") if tag.strip()]
            points = []
            for value in route_points or []:
                a, b = value.split(",")
                points.append(Point(latitude=float(a), longitude=float(b)))
            context = FeedContext(
                lat=lat,
                lon=lon,
                interests=tags,
                navigation_active=navigation_active,
                destination_lat=destination_lat,
                destination_lon=destination_lon,
                eta_minutes=eta_minutes,
                route_points=points,
                route_link_ids=route_link_ids or [],
                route_link_namespace=route_link_namespace,
            )
        except (ValueError, ValidationError):
            raise HTTPException(
                422, "Invalid feed query: check coordinate pairs, interests and navigation fields"
            )
        result = build_feed(
            store.all(settings.data_mode),
            context,
            utcnow(),
            DataMode(settings.data_mode.upper()),
            routing=routing,
        )
        if settings.data_mode != "mock":
            from .models import Diagnostic

            seen = set()
            for collected in store.recent_collections():
                if collected["provider"] not in seen and collected["status"] == "FAILED":
                    result.diagnostics.append(
                        Diagnostic(
                            code="SOURCE_UNAVAILABLE", message=collected["provider"] + ":" + collected["code"]
                        )
                    )
                seen.add(collected["provider"])
        if not (result.top3 or result.queue or result.alerts):
            from .models import Diagnostic

            result.diagnostics.append(
                Diagnostic(code="NO_ELIGIBLE_CONTENT", message="수집 상태와 필터를 확인하세요")
            )
        return result

    @app.get("/api/v1/contents/{content_id}", response_model=ContentDetail)
    def detail(content_id: str):
        item = store.get(content_id, settings.data_mode)
        if item is None:
            raise HTTPException(404, "CONTENT_NOT_FOUND")
        now = utcnow()
        return {
            **item.model_dump(mode="json"),
            "is_expired": item.expires_at <= now,
            "tts_eligible": voice_allowed(item) and unavailable_reason(item, now) is None,
        }

    @app.post("/api/v1/contents/{content_id}/explain", response_model=ExplainResponse)
    async def explain(content_id: str, request: ExplainRequest | None = None):
        item = store.get(content_id, settings.data_mode)
        if item is None:
            raise HTTPException(404, "CONTENT_NOT_FOUND")
        if not tts_allowed(item):
            raise HTTPException(403, "RIGHTS_NOT_CLEARED")
        if unavailable_reason(item, utcnow()) is not None:
            raise HTTPException(409, "CONTENT_EXPIRED_OR_UNVERIFIED")
        return await llm.explain(item, (request or ExplainRequest()).question)

    return app
