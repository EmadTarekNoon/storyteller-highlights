"""Sport profile interface.

A profile encapsulates everything sport-specific: how events change the score,
how important each event is for ranking, which events must always be shown, how
captions read, and which cover/info pages make sense. Adding a new sport means
writing one profile and registering it - the core pipeline and web viewer stay
unchanged.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Caption, Event, Match, Score, ScoreDelta


class SportProfile(ABC):
    #: Sport names (as they appear in the feed) this profile serves.
    handles: tuple[str, ...] = ()

    #: How many highlight pages to aim for in a Story.
    target_highlights: int = 10

    # -- scoring -----------------------------------------------------------
    @abstractmethod
    def score_delta(self, event: Event, match: Match) -> ScoreDelta:
        """Return how ``event`` changes the score (zero for most events)."""

    # -- ranking -----------------------------------------------------------
    @abstractmethod
    def weight(self, event: Event) -> float:
        """Importance of an event for ranking (higher = more likely selected)."""

    def must_include(self, event: Event) -> bool:
        """Events that should always appear regardless of the slot budget."""
        return False

    # -- narration ---------------------------------------------------------
    @abstractmethod
    def caption(self, event: Event, score: Score, match: Match) -> Caption:
        """Produce headline/caption/explanation text for a highlight page."""

    # -- structural pages --------------------------------------------------
    @abstractmethod
    def cover(self, match: Match, final: Score) -> dict:
        """Build the cover page dict."""

    def info_pages(self, match: Match, final: Score, events: list[Event]) -> list[dict]:
        """Optional trailing info/stats pages. Default: none."""
        return []

    def metrics(self, match: Match, final: Score, events: list[Event]) -> dict:
        """Free-form metrics recorded on the Story. Default: empty."""
        return {}

    # -- helpers -----------------------------------------------------------
    def side_of(self, event: Event, match: Match) -> str:
        """Return 'home'/'away'/'' for the event's team."""
        if event.team is None:
            return ""
        if match.home and event.team.id == match.home.id:
            return "home"
        if match.away and event.team.id == match.away.id:
            return "away"
        return "home" if event.team.home else "away"
