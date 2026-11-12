from typing import Protocol

from .models import Content, DataMode, FeedContext, TravelAssessment


class RoutingProvider(Protocol):
    def assess(self, context: FeedContext, content: Content) -> TravelAssessment: ...


class UnverifiedRouting:
    def assess(self, context: FeedContext, content: Content) -> TravelAssessment:
        return TravelAssessment()


class DemoRouting(UnverifiedRouting):
    """Fixture-only driving time; never claims a real route calculation."""

    def assess(self, context: FeedContext, content: Content) -> TravelAssessment:
        if content.data_mode == DataMode.MOCK:
            return TravelAssessment(status="SIMULATED", minutes=25, provider="fixture-only")
        return super().assess(context, content)
