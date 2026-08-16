"""Score-agnostic fallback profile for sports without a dedicated profile.

It cannot know a sport's scoring rules, so it swaps in a ``NullScorer`` (score
stays 0-0) and a ``KeywordRanker`` (importance from universal keywords + whether
a player is named). The default ``TemplateNarrator`` and ``SummaryComposer`` then
produce a valid, readable Story - the composer emits no scoreboard because there
is no scoring. This guarantees an unfamiliar sport still yields a valid Story
rather than an error.
"""

from __future__ import annotations

from functools import cached_property

from ..behaviors.ranking import KeywordRanker, Ranker
from ..behaviors.scoring import NullScorer, Scorer
from .base import SportProfile


class GenericProfile(SportProfile):
    handles = ()  # selected only as an explicit fallback
    target_highlights = 10

    @cached_property
    def scorer(self) -> Scorer:
        return NullScorer()

    @cached_property
    def ranker(self) -> Ranker:
        return KeywordRanker(must_include_types=self.must_include_types)
