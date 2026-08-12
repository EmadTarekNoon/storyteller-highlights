"""Score-agnostic fallback profile for sports without a dedicated profile.

It cannot know a sport's scoring rules, so it keeps the score at 0-0 and ranks
events by simple, universally-reasonable heuristics (keyword importance +
whether a player is named). This guarantees an unfamiliar sport still yields a
valid, readable Story rather than an error.
"""

from __future__ import annotations

from ..models import Caption, Event, Match, Score, ScoreDelta
from .base import SportProfile

# Keywords that tend to mark important moments across many sports.
IMPORTANT_KEYWORDS = (
    "goal", "try", "point", "score", "touchdown", "run", "wicket",
    "card", "penalty", "foul", "save", "miss", "shot", "sent off",
)


class GenericProfile(SportProfile):
    handles = ()  # selected only as an explicit fallback
    target_highlights = 10

    def score_delta(self, event: Event, match: Match) -> ScoreDelta:
        return ScoreDelta()

    def weight(self, event: Event) -> float:
        text = f"{event.type} {event.comment}".lower()
        score = 10.0
        for i, kw in enumerate(IMPORTANT_KEYWORDS):
            if kw in text:
                score = max(score, 100.0 - i * 3)
        if event.player:
            score += 5.0
        return score

    def caption(self, event: Event, score: Score, match: Match) -> Caption:
        minute = f"{event.minute}'"
        team = event.team.name if event.team else ""
        headline = f"{minute} {event.type.title()}" + (f" - {team}" if team else "")
        caption = event.comment or event.type.title()
        return Caption(headline, caption, "")

    def cover(self, match: Match, final: Score) -> dict:
        home = match.home.name if match.home else "Home"
        away = match.away.name if match.away else "Away"
        subparts = [p for p in (match.sport, match.competition, match.venue, match.date) if p]
        return {"headline": f"{home} vs {away}", "subheadline": " | ".join(subparts)}

    def info_pages(self, match: Match, final: Score, events: list[Event]) -> list[dict]:
        # Score-agnostic: don't fabricate a 0-0 scoreboard for an unknown sport.
        return []
