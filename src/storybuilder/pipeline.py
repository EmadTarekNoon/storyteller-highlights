"""Sport-agnostic core: turn a :class:`Match` into a ranked, narrated Story.

Flow: compute a running score across all events (so captions can reference the
scoreline at any moment) -> rank events using the profile -> select a
well-paced, chronological set of highlights -> hand off to story assembly.
"""

from __future__ import annotations

from .models import Event, Match, RankedEvent, Score
from .profiles.base import SportProfile


def compute_running_scores(match: Match, profile: SportProfile) -> dict[str, Score]:
    """Return a map of event ``raw_id`` (or index key) -> score *after* that event."""

    scores: dict[str, Score] = {}
    running = Score()
    for idx, event in enumerate(match.events):
        delta = profile.score_delta(event, match)
        running = running.add(home=delta.home, away=delta.away)
        scores[_key(event, idx)] = running
    return scores


def final_score(match: Match, profile: SportProfile) -> Score:
    running = Score()
    for event in match.events:
        delta = profile.score_delta(event, match)
        running = running.add(home=delta.home, away=delta.away)
    return running


def select_highlights(match: Match, profile: SportProfile) -> list[RankedEvent]:
    """Choose which events become highlight pages.

    All ``must_include`` events are kept; the remaining slots (up to the
    profile's target) are filled by the highest-weighted events. The final list
    is returned in chronological order.
    """

    running_scores = compute_running_scores(match, profile)
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
        score = running_scores[_key(event, idx)]
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


def _key(event: Event, idx: int) -> str:
    return event.raw_id or f"idx-{idx}"
