"""Narration seam: turn a selected event into a headline + caption.

``TemplateNarrator`` is the deterministic default (minute + label + team, with a
scoreline for scoring events). This is the seam a future ``LLMNarrator`` slots
into (see docs/ROADMAP.md) - the pipeline depends only on this interface, not on
how the text is produced.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import Caption, Event, Match, Score
from .common import label_for, scoreline


@runtime_checkable
class Narrator(Protocol):
    def caption(self, event: Event, score: Score, match: Match) -> Caption: ...


class TemplateNarrator:
    """Generic caption: minute + label + team; scoreline for scoring events."""

    def __init__(self, terms: dict[str, str], scoring: dict[str, int]):
        self._terms = terms
        self._scoring = scoring

    def caption(self, event: Event, score: Score, match: Match) -> Caption:
        minute = f"{event.minute}'"
        team = event.team.name if event.team else ""
        label = label_for(event.type, self._terms)
        headline = f"{minute} {label}" + (f" - {team}" if team else "")
        if event.type in self._scoring:
            headline = f"{minute} {label} - {scoreline(match, score)}"
        body = event.comment or label
        return Caption(headline, body, "")
