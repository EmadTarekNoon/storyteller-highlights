"""Internal data model shared across the sport-agnostic core.

These dataclasses are what *every* adapter must produce and what *every* sport
profile consumes. Keeping the model free of provider- and sport-specific detail
is what lets the pipeline and viewer stay generic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Team:
    """A participating team, resolved from the feed's team references."""

    id: str
    name: str
    code: str = ""
    home: bool = False


@dataclass(frozen=True)
class Event:
    """A single normalized match event.

    Adapters are responsible for coercing raw feed values (which are often
    strings and stored newest-first) into this normalized, chronologically
    sortable shape.
    """

    type: str
    period: int
    minute: int
    second: int
    team: Optional[Team] = None
    player: Optional[str] = None
    player2: Optional[str] = None
    comment: str = ""
    raw_id: str = ""

    @property
    def sort_key(self) -> tuple[int, int, int]:
        return (self.period, self.minute, self.second)


@dataclass
class Match:
    """A whole match: metadata plus the chronologically ordered events.

    This is the boundary object between adapters (which build it) and the
    pipeline/profile (which consume it). Nothing here is sport-specific beyond
    the free-form ``sport`` label used to select a profile.
    """

    home: Team
    away: Team
    events: list[Event]
    sport: str = ""
    competition: str = ""
    venue: str = ""
    date: str = ""
    source: str = ""
    match_id: str = ""

    def teams(self) -> list[Team]:
        return [self.home, self.away]


@dataclass(frozen=True)
class Score:
    """A running scoreline keyed by team id."""

    home: int = 0
    away: int = 0

    def add(self, *, home: int = 0, away: int = 0) -> "Score":
        return Score(self.home + home, self.away + away)


@dataclass(frozen=True)
class ScoreDelta:
    """How much an event changes the score, per side."""

    home: int = 0
    away: int = 0

    @property
    def is_zero(self) -> bool:
        return self.home == 0 and self.away == 0


@dataclass(frozen=True)
class Caption:
    """Text a profile produces for a highlight page."""

    headline: str
    caption: str
    explanation: str = ""


@dataclass(frozen=True)
class StatRow:
    """One row of the full-time home-vs-away comparison.

    ``types`` are the event types counted for the row. ``attribute`` decides
    which side each matching event is credited to: ``"acting"`` (the event's own
    team, the usual case) or ``"opponent"`` (e.g. corners, where the feed's team
    reference is the conceding side).
    """

    label: str
    types: frozenset[str]
    attribute: str = "acting"


@dataclass
class RankedEvent:
    """An event selected for the Story, with its score/weight context."""

    event: Event
    score: Score
    weight: float
    explanation: str


# --- Page / Story builders -------------------------------------------------
# The output schema (schema/story.schema.json) defines three page types.
# These helpers centralize construction so field names stay consistent and the
# assembled dict always matches the schema.


def cover_page(headline: str, image: str, subheadline: str = "") -> dict:
    page: dict = {"type": "cover", "headline": headline, "image": image}
    if subheadline:
        page["subheadline"] = subheadline
    return page


def highlight_page(
    minute: int,
    headline: str,
    caption: str,
    image: str = "",
    explanation: str = "",
) -> dict:
    page: dict = {
        "type": "highlight",
        "minute": minute,
        "headline": headline,
        "caption": caption,
    }
    if image:
        page["image"] = image
    if explanation:
        page["explanation"] = explanation
    return page


def info_page(headline: str, body: str = "") -> dict:
    page: dict = {"type": "info", "headline": headline}
    if body:
        page["body"] = body
    return page
