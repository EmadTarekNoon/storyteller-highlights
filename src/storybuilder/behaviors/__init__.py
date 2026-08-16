"""Swappable behaviour collaborators used by :class:`SportProfile`.

Each seam is a small ``Protocol`` with a declarative default so a profile stays a
thin bag of configuration, while any single aspect (scoring, ranking, narration,
composition, selection) can be replaced independently.
"""

from __future__ import annotations

from .composition import PageComposer, SummaryComposer
from .narration import Narrator, TemplateNarrator
from .ranking import KeywordRanker, Ranker, WeightRanker
from .scoring import AttributeScorer, NullScorer, Scorer
from .selection import HighlightSelector, WeightedSelector

__all__ = [
    "Scorer",
    "AttributeScorer",
    "NullScorer",
    "Ranker",
    "WeightRanker",
    "KeywordRanker",
    "Narrator",
    "TemplateNarrator",
    "PageComposer",
    "SummaryComposer",
    "HighlightSelector",
    "WeightedSelector",
]
