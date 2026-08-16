"""Small, dependency-free helpers shared by the behaviour collaborators.

Keeping these here (rather than as methods on ``SportProfile``) lets every
collaborator - scorer, narrator, composer - share the exact same team-side and
scoreline logic without importing the profile, which would create a cycle.
"""

from __future__ import annotations

from ..models import Event, Match, Score


def side_of(event: Event, match: Match) -> str:
    """Return ``'home'`` / ``'away'`` / ``''`` for the event's team."""
    if event.team is None:
        return ""
    if match.home and event.team.id == match.home.id:
        return "home"
    if match.away and event.team.id == match.away.id:
        return "away"
    return "home" if event.team.home else "away"


def label_for(event_type: str, terms: dict[str, str]) -> str:
    """Short display label for an event type (from ``terms`` or Title Case)."""
    return terms.get(event_type, event_type.title())


def scoreline(match: Match, score: Score) -> str:
    home = match.home.name if match.home else "Home"
    away = match.away.name if match.away else "Away"
    return f"{home} {score.home}-{score.away} {away}"
