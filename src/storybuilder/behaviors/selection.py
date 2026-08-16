"""Selection seam: choose which events become highlight pages, and in what order.

``WeightedSelector`` is the default pacing strategy: keep every must-include
event, fill the remaining slots by descending weight, then return the set in
chronological order. This is the seam for smarter pacing (team/half balancing,
dedup of near-duplicate beats) - see docs/ROADMAP.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from ..models import Event, Match, RankedEvent, Score

if TYPE_CHECKING:  # avoid a runtime import cycle with profiles.base
    from ..profiles.base import SportProfile


@runtime_checkable
class HighlightSelector(Protocol):
    def select(self, match: Match, profile: SportProfile) -> list[RankedEvent]: ...


def running_scores(match: Match, profile: SportProfile) -> dict[str, Score]:
    """Map of event key -> score *after* that event (uses the profile's scorer)."""
    scores: dict[str, Score] = {}
    running = Score()
    for idx, event in enumerate(match.events):
        delta = profile.score_delta(event, match)
        running = running.add(home=delta.home, away=delta.away)
        scores[event_key(event, idx)] = running
    return scores


def event_key(event: Event, idx: int) -> str:
    return event.raw_id or f"idx-{idx}"


class WeightedSelector:
    def select(self, match: Match, profile: SportProfile) -> list[RankedEvent]:
        scores = running_scores(match, profile)
        target = profile.target_highlights
        noise = getattr(profile, "noise_types", frozenset())

        scored: list[tuple[float, int, Event]] = []
        forced: list[tuple[int, Event]] = []
        for idx, event in enumerate(match.events):
            if event.type in noise:
                continue
            if profile.must_include(event):
                forced.append((idx, event))
            else:
                scored.append((profile.weight(event), idx, event))

        chosen_idx = {idx for idx, _ in forced}
        remaining = max(target - len(chosen_idx), 0)
        scored.sort(key=lambda t: (t[0], -t[1]), reverse=True)
        for _weight, idx, _event in scored[:remaining]:
            chosen_idx.add(idx)

        ranked: list[RankedEvent] = []
        for idx, event in enumerate(match.events):
            if idx not in chosen_idx:
                continue
            score = scores[event_key(event, idx)]
            caption = profile.caption(event, score, match)
            ranked.append(
                RankedEvent(
                    event=event,
                    score=score,
                    weight=profile.weight(event),
                    explanation=caption.explanation,
                )
            )
        return ranked
