"""Sport profile interface.

A profile encapsulates everything sport-specific: how events change the score,
how important each event is for ranking, which events must always be shown, how
captions read, and which cover/info pages make sense.

Adding a new sport is meant to be tiny: subclass :class:`SportProfile`, set a
handful of **declarative class attributes** (``handles``, ``weights``,
``scoring``, ``must_include_types``, ``terms``), and drop the file in this
package. It is auto-discovered and registered - no edits to any registry list.
Everything below has a working default driven by those attributes, so you only
override a method when a sport needs genuinely custom behaviour (see
``soccer.py`` for a rich example).
"""

from __future__ import annotations

from ..models import Caption, Event, Match, Score, ScoreDelta

# Structural/administrative events that never make good standalone highlights.
DEFAULT_NOISE = frozenset(
    {"lineup", "start", "end", "end 1", "end 2", "start delay", "end delay", "kickoff"}
)


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

    # -- scoring -----------------------------------------------------------
    def score_delta(self, event: Event, match: Match) -> ScoreDelta:
        """Default: award ``scoring[type]`` points to the acting side."""
        points = self.scoring.get(event.type, 0)
        if not points:
            return ScoreDelta()
        side = self.side_of(event, match)
        if event.type in self.own_types:
            side = "away" if side == "home" else "home"
        return ScoreDelta(home=points) if side == "home" else ScoreDelta(away=points)

    # -- ranking -----------------------------------------------------------
    def weight(self, event: Event) -> float:
        return self.weights.get(event.type, self.default_weight)

    def must_include(self, event: Event) -> bool:
        return event.type in self.must_include_types

    # -- narration ---------------------------------------------------------
    def caption(self, event: Event, score: Score, match: Match) -> Caption:
        """Generic caption: minute + label + team, scoreline for scoring events."""
        minute = f"{event.minute}'"
        team = event.team.name if event.team else ""
        label = self.label_for(event.type)
        headline = f"{minute} {label}" + (f" - {team}" if team else "")
        if event.type in self.scoring:
            headline = f"{minute} {label} - {self.scoreline(match, score)}"
        body = event.comment or label
        return Caption(headline, body, "")

    # -- structural pages --------------------------------------------------
    def cover(self, match: Match, final: Score) -> dict:
        home = match.home.name if match.home else "Home"
        away = match.away.name if match.away else "Away"
        subparts = [p for p in (match.sport, match.competition, match.venue, match.date) if p]
        if self.scoring and (final.home or final.away):
            headline = f"{home} {final.home}-{final.away} {away}"
        else:
            headline = f"{home} vs {away}"
        return {"headline": headline, "subheadline": " | ".join(subparts)}

    def info_pages(self, match: Match, final: Score, events: list[Event]) -> list[dict]:
        """Default full-time page: scoreboard + counts of the ranked event types."""
        counts: dict[str, int] = {}
        for e in events:
            if e.type in self.weights:
                counts[e.type] = counts.get(e.type, 0) + 1
        rows = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
        body = "\n".join(f"{self.label_for(t)}: {n}" for t, n in rows)
        page = {
            "type": "info",
            "headline": "Full time",
            "home_team": match.home.name if match.home else "Home",
            "away_team": match.away.name if match.away else "Away",
            "home_code": (match.home.code if match.home else "") or "HOME",
            "away_code": (match.away.code if match.away else "") or "AWAY",
            "home_score": final.home,
            "away_score": final.away,
            "body": body,
        }
        return [page]

    def metrics(self, match: Match, final: Score, events: list[Event]) -> dict:
        return {
            "final_score": {"home": final.home, "away": final.away},
            "total_events": len(events),
        }

    # -- helpers -----------------------------------------------------------
    def label_for(self, event_type: str) -> str:
        return self.terms.get(event_type, event_type.title())

    def scoreline(self, match: Match, score: Score) -> str:
        home = match.home.name if match.home else "Home"
        away = match.away.name if match.away else "Away"
        return f"{home} {score.home}-{score.away} {away}"

    def side_of(self, event: Event, match: Match) -> str:
        """Return 'home'/'away'/'' for the event's team."""
        if event.team is None:
            return ""
        if match.home and event.team.id == match.home.id:
            return "home"
        if match.away and event.team.id == match.away.id:
            return "away"
        return "home" if event.team.home else "away"
