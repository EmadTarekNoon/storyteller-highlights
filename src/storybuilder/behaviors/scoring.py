"""Scoring seam: how an event changes the running score.

``Scorer`` is the swappable interface; ``AttributeScorer`` derives behaviour
from a profile's declarative ``scoring`` / ``own_types`` maps (the common case),
and ``NullScorer`` is used by score-agnostic sports (the generic fallback).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import Event, Match, ScoreDelta
from .common import side_of


@runtime_checkable
class Scorer(Protocol):
    def score_delta(self, event: Event, match: Match) -> ScoreDelta: ...


class AttributeScorer:
    """Award ``scoring[type]`` points to the acting side.

    Types listed in ``own_types`` (e.g. own goals) credit the *opponent*.
    """

    def __init__(self, scoring: dict[str, int], own_types: frozenset[str]):
        self._scoring = scoring
        self._own = own_types

    def score_delta(self, event: Event, match: Match) -> ScoreDelta:
        points = self._scoring.get(event.type, 0)
        if not points:
            return ScoreDelta()
        side = side_of(event, match)
        if event.type in self._own:
            side = "away" if side == "home" else "home"
        return ScoreDelta(home=points) if side == "home" else ScoreDelta(away=points)


class NullScorer:
    """Never changes the score - for sports whose scoring rules are unknown."""

    def score_delta(self, event: Event, match: Match) -> ScoreDelta:
        return ScoreDelta()
