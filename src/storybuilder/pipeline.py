"""Sport-agnostic core: turn a :class:`Match` into a ranked, narrated Story.

Flow: compute a running score across all events (so captions can reference the
scoreline at any moment) -> rank events using the profile -> select a
well-paced, chronological set of highlights -> hand off to story assembly.

The selection algorithm itself lives behind the profile's ``selector`` seam
(``behaviors/selection.py``); these functions are thin, stable entry points that
the rest of the code (and the tests) use.
"""

from __future__ import annotations

from .behaviors.selection import event_key
from .behaviors.selection import running_scores as _running_scores
from .models import Match, RankedEvent, Score
from .profiles.base import SportProfile


def compute_running_scores(match: Match, profile: SportProfile) -> dict[str, Score]:
    """Return a map of event ``raw_id`` (or index key) -> score *after* that event."""
    return _running_scores(match, profile)


def final_score(match: Match, profile: SportProfile) -> Score:
    running = Score()
    for event in match.events:
        delta = profile.score_delta(event, match)
        running = running.add(home=delta.home, away=delta.away)
    return running


def select_highlights(match: Match, profile: SportProfile) -> list[RankedEvent]:
    """Choose which events become highlight pages (delegates to the selector)."""
    return profile.selector.select(match, profile)


def _key(event, idx: int) -> str:
    return event_key(event, idx)
