"""Soccer sport profile: scoring, ranking weights and caption templates.

Weights and event handling were designed from the event-type distribution in
the sample feed, but the pipeline tolerates unseen types via a default weight,
so a slightly different soccer feed still produces a sensible Story.

Soccer keeps the declarative config on the profile but swaps in two richer
collaborators: a ``SoccerNarrator`` (commentary-driven goal/card/penalty
captions) and a ``SoccerComposer`` (scoreline cover + detailed metrics).
"""

from __future__ import annotations

from functools import cached_property

from ..behaviors.composition import SummaryComposer
from ..behaviors.narration import Narrator
from ..models import Caption, Event, Match, Score, StatRow
from .base import SportProfile

# Event types that increase the acting team's score.
GOAL_TYPES = {"goal", "penalty goal", "own goal"}

# Importance weights. Higher => more likely to be chosen as a highlight.
WEIGHTS: dict[str, float] = {
    "goal": 100.0,
    "penalty goal": 100.0,
    "own goal": 95.0,
    "red card": 85.0,
    "penalty won": 75.0,
    "penalty lost": 74.0,
    "penalty miss": 73.0,
    "post": 60.0,
    "attempt saved": 55.0,
    "attempt blocked": 45.0,
    "miss": 42.0,
    "second yellow card": 84.0,
    "yellow card": 40.0,
    "offside": 25.0,
    "substitution": 22.0,
    "corner": 18.0,
    "free kick won": 10.0,
    "free kick lost": 8.0,
    "added time": 6.0,
    "start delay": 5.0,
    "end delay": 5.0,
    "start": 4.0,
    "lineup": 3.0,
}

# Events that must always appear in the Story if present.
ALWAYS_INCLUDE = GOAL_TYPES | {"red card", "second yellow card", "penalty won", "penalty lost"}

DEFAULT_WEIGHT = 15.0


class SoccerProfile(SportProfile):
    # Declarative config — the base class turns these into scoring, ranking and
    # must-include behaviour. Soccer swaps in richer narration/composition below.
    handles = ("soccer", "football")
    target_highlights = 10
    weights = WEIGHTS
    default_weight = DEFAULT_WEIGHT
    must_include_types = frozenset(ALWAYS_INCLUDE)
    scoring = {"goal": 1, "penalty goal": 1, "own goal": 1}
    own_types = frozenset({"own goal"})

    # Full-time summary rows (rendered as home-vs-away comparison bars).
    score_label = "Goals"
    summary_stats = (
        StatRow(
            "Shots", frozenset({"goal", "penalty goal", "miss", "attempt saved", "attempt blocked", "post"})
        ),
        StatRow("On target", frozenset({"goal", "penalty goal", "attempt saved"})),
        # Corners: the feed credits teamRef1 to the *conceding* side, so flip it.
        StatRow("Corners", frozenset({"corner"}), attribute="opponent"),
        StatRow("Offsides", frozenset({"offside"})),
        StatRow("Fouls", frozenset({"free kick lost"})),
        StatRow("Yellow cards", frozenset({"yellow card", "second yellow card"})),
    )

    @cached_property
    def narrator(self) -> Narrator:
        return SoccerNarrator()

    @cached_property
    def composer(self) -> SummaryComposer:
        return SoccerComposer(self.scoring, self.score_label, self.summary_stats)


class SoccerNarrator:
    """Commentary-driven soccer captions (goals, cards, penalties, chances)."""

    def caption(self, event: Event, score: Score, match: Match) -> Caption:
        minute = _clock(event)
        team = event.team.name if event.team else ""
        player = event.player or _player_from_comment(event.comment) or ""
        line = _scoreline(match, score)

        if event.type in GOAL_TYPES:
            label = "PENALTY GOAL" if event.type == "penalty goal" else "GOAL"
            headline = f"{minute} {label} - {line}"
            # Prefer the rich source commentary (scorer, shot type, assist).
            detail = _strip_scoreline_prefix(event.comment)
            if not detail:
                who = f"{player} ({team})" if player and team else player or team
                detail = f"{who} scores." if who else "Goal!"
            caption = f"{detail} {line}."
            return Caption(headline, _clean(caption), f"Goal at {minute} made it {line}.")

        if event.type in {"yellow card", "second yellow card", "red card"}:
            card = event.type.replace(" card", "").title()
            headline = f"{minute} {card} card"
            caption = f"{player} ({team}) is booked." if player and team else event.comment
            return Caption(headline, _clean(caption) or event.comment, "Disciplinary moment.")

        if event.type in {"penalty won", "penalty lost"}:
            headline = f"{minute} Penalty {'awarded' if event.type == 'penalty won' else 'decision'}"
            return Caption(headline, event.comment or f"Penalty to {team}.", "Penalty-box drama.")

        if event.type == "substitution":
            headline = f"{minute} Substitution - {team}"
            return Caption(headline, event.comment or "Change made.", "Tactical change.")

        if event.type in {"post", "attempt saved", "attempt blocked", "miss"}:
            headline = f"{minute} Big chance - {team}"
            return Caption(headline, event.comment or "Close call.", "A notable goalscoring chance.")

        # Generic fallback for any other soccer event type.
        headline = f"{minute} {event.type.title()}" + (f" - {team}" if team else "")
        return Caption(headline, event.comment or event.type.title(), "")


class SoccerComposer(SummaryComposer):
    """Soccer cover (always a scoreline) + richer per-type metrics."""

    def cover(self, match: Match, final: Score) -> dict:
        home = match.home.name if match.home else "Home"
        away = match.away.name if match.away else "Away"
        subparts = [p for p in (match.competition, match.venue, match.date) if p]
        return {"headline": f"{home} {final.home}-{final.away} {away}", "subheadline": " | ".join(subparts)}

    def metrics(self, match: Match, final: Score, events: list[Event]) -> dict:
        counts = _count_types(events)
        return {
            "final_score": {
                "home": final.home,
                "away": final.away,
                "home_team": match.home.name if match.home else "",
                "away_team": match.away.name if match.away else "",
            },
            "goals": counts.get("goal", 0) + counts.get("penalty goal", 0),
            "event_counts": counts,
            "total_events": len(events),
        }


def _scoreline(match: Match, score: Score) -> str:
    home = match.home.name if match.home else "Home"
    away = match.away.name if match.away else "Away"
    return f"{home} {score.home}-{score.away} {away}"


def _clock(event: Event) -> str:
    return f"{event.minute}'"


def _count_types(events: list[Event]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in events:
        counts[e.type] = counts.get(e.type, 0) + 1
    return counts


def _clean(text: str) -> str:
    return " ".join(text.split()).replace(" .", ".").strip()


def _strip_scoreline_prefix(comment: str) -> str:
    """Drop the leading 'Goal! Celtic 1, Kilmarnock 0.' so we can append our own.

    Keeps the descriptive remainder (scorer, shot type, assist) which is the
    valuable part of the commentary.
    """
    if not comment:
        return ""
    text = comment.strip()
    lowered = text.lower()
    if lowered.startswith("goal"):
        # Remove up to and including the first sentence (the score summary).
        parts = text.split(". ", 1)
        if len(parts) == 2:
            return parts[1].strip()
        return ""
    return text


def _player_from_comment(comment: str) -> str:
    # Best-effort: many comments start with "<Player> (<Team>) ...".
    if "(" in comment:
        return comment.split("(", 1)[0].strip(" .")
    return ""
