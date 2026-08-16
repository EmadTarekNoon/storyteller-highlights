"""Ranking seam: how important each event is and which must always appear.

``WeightRanker`` reads a profile's declarative ``weights`` map; ``KeywordRanker``
is a sport-agnostic heuristic used by the generic fallback profile.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import Event

# Keywords that tend to mark important moments across many sports.
IMPORTANT_KEYWORDS = (
    "goal",
    "try",
    "point",
    "score",
    "touchdown",
    "run",
    "wicket",
    "card",
    "penalty",
    "foul",
    "save",
    "miss",
    "shot",
    "sent off",
)


@runtime_checkable
class Ranker(Protocol):
    def weight(self, event: Event) -> float: ...
    def must_include(self, event: Event) -> bool: ...


class WeightRanker:
    """Importance from a declarative ``weights`` map (with a default fallback)."""

    def __init__(
        self,
        weights: dict[str, float],
        default_weight: float,
        must_include_types: frozenset[str],
    ):
        self._weights = weights
        self._default = default_weight
        self._must = must_include_types

    def weight(self, event: Event) -> float:
        return self._weights.get(event.type, self._default)

    def must_include(self, event: Event) -> bool:
        return event.type in self._must


class KeywordRanker:
    """Sport-agnostic heuristic: keyword importance + a bonus for named players."""

    def __init__(
        self,
        keywords: tuple[str, ...] = IMPORTANT_KEYWORDS,
        must_include_types: frozenset[str] = frozenset(),
    ):
        self._keywords = keywords
        self._must = must_include_types

    def weight(self, event: Event) -> float:
        text = f"{event.type} {event.comment}".lower()
        score = 10.0
        for i, kw in enumerate(self._keywords):
            if kw in text:
                score = max(score, 100.0 - i * 3)
        if event.player:
            score += 5.0
        return score

    def must_include(self, event: Event) -> bool:
        return event.type in self._must
