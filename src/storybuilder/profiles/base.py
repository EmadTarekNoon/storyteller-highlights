"""Sport profile: a declarative bag of configuration that wires behaviour seams.

A profile encapsulates everything sport-specific: how events change the score,
how important each event is for ranking, which events must always be shown, how
captions read, and which cover/summary pages make sense.

Adding a new sport is meant to be tiny: subclass :class:`SportProfile`, set a
handful of **declarative class attributes** (``handles``, ``weights``,
``scoring``, ``must_include_types``, ``terms``), and drop the file in this
package. It is auto-discovered and registered - no edits to any registry list.

Internally the profile owns five swappable collaborators (``scorer``, ``ranker``,
``narrator``, ``composer``, ``selector``) built from those attributes. Override a
single collaborator (see ``soccer.py``'s ``SoccerNarrator``) when a sport needs
genuinely custom behaviour, or override a method for a one-off tweak - the
public methods below simply delegate to the collaborators.
"""

from __future__ import annotations

from functools import cached_property

from ..behaviors.common import label_for, scoreline, side_of
from ..behaviors.composition import PageComposer, SummaryComposer
from ..behaviors.narration import Narrator, TemplateNarrator
from ..behaviors.ranking import Ranker, WeightRanker
from ..behaviors.scoring import AttributeScorer, Scorer
from ..behaviors.selection import HighlightSelector, WeightedSelector
from ..models import Caption, Event, Match, RankedEvent, Score, ScoreDelta, StatRow

# Structural/administrative events that never make good standalone highlights.
DEFAULT_NOISE = frozenset({"lineup", "start", "end", "end 1", "end 2", "start delay", "end delay", "kickoff"})


class SportProfile:
    # -- declarative configuration (override these in a subclass) ----------
    #: Sport names (as they appear in the feed's ``sport.name``) this serves.
    handles: tuple[str, ...] = ()
    #: How many highlight pages to aim for in a Story.
    target_highlights: int = 10
    #: event type -> ranking importance (higher = more likely selected).
    weights: dict[str, float] = {}
    #: weight used for event types not present in ``weights``.
    default_weight: float = 15.0
    #: event types that always appear regardless of the slot budget.
    must_include_types: frozenset[str] = frozenset()
    #: event type -> points awarded to the acting team (drives running score).
    scoring: dict[str, int] = {}
    #: scoring event types that credit the *opponent* (e.g. own goals).
    own_types: frozenset[str] = frozenset()
    #: event type -> short label used in headlines (defaults to Title Case).
    terms: dict[str, str] = {}
    #: event types treated as noise (excluded from highlights).
    noise_types: frozenset[str] = DEFAULT_NOISE
    #: label for the score row on the full-time summary (e.g. "Goals", "Points").
    score_label: str = "Score"
    #: rows for the full-time home-vs-away comparison (see :class:`StatRow`).
    summary_stats: tuple[StatRow, ...] = ()

    def __init__(self, config: dict | None = None):
        """Optionally override the declarative class attributes from ``config``.

        ``config`` is a raw (JSON-shaped) dict; it is applied before any
        collaborator is built, so externalized tuning takes full effect.
        """
        if config:
            from ..config import apply_config

            apply_config(self, config)

    # -- collaborators (override a property to swap one aspect) ------------
    @cached_property
    def scorer(self) -> Scorer:
        return AttributeScorer(self.scoring, self.own_types)

    @cached_property
    def ranker(self) -> Ranker:
        return WeightRanker(self.weights, self.default_weight, self.must_include_types)

    @cached_property
    def narrator(self) -> Narrator:
        return TemplateNarrator(self.terms, self.scoring)

    @cached_property
    def composer(self) -> PageComposer:
        return SummaryComposer(self.scoring, self.score_label, self.summary_stats)

    @cached_property
    def selector(self) -> HighlightSelector:
        return WeightedSelector()

    # -- public API (delegates to the collaborators) ----------------------
    def score_delta(self, event: Event, match: Match) -> ScoreDelta:
        return self.scorer.score_delta(event, match)

    def weight(self, event: Event) -> float:
        return self.ranker.weight(event)

    def must_include(self, event: Event) -> bool:
        return self.ranker.must_include(event)

    def caption(self, event: Event, score: Score, match: Match) -> Caption:
        return self.narrator.caption(event, score, match)

    def cover(self, match: Match, final: Score) -> dict:
        return self.composer.cover(match, final)

    def info_pages(self, match: Match, final: Score, events: list[Event]) -> list[dict]:
        return self.composer.info_pages(match, final, events)

    def metrics(self, match: Match, final: Score, events: list[Event]) -> dict:
        return self.composer.metrics(match, final, events)

    def select_highlights(self, match: Match) -> list[RankedEvent]:
        return self.selector.select(match, self)

    # -- helpers (kept for convenience / backward compatibility) ----------
    def label_for(self, event_type: str) -> str:
        return label_for(event_type, self.terms)

    def scoreline(self, match: Match, score: Score) -> str:
        return scoreline(match, score)

    def side_of(self, event: Event, match: Match) -> str:
        return side_of(event, match)
