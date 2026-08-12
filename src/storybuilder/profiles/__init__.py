"""Profile registry keyed on sport name, with a generic fallback."""

from __future__ import annotations

from .base import SportProfile
from .generic import GenericProfile
from .soccer import SoccerProfile

_PROFILES: list[type[SportProfile]] = [SoccerProfile]


def available_sports() -> list[str]:
    sports: list[str] = []
    for p in _PROFILES:
        sports.extend(p.handles)
    return sports


def get_profile(sport: str | None) -> SportProfile:
    """Return a profile for ``sport`` (case-insensitive), else the generic one.

    ``sport`` may be the feed's sport name or an explicit ``--sport`` override.
    """

    key = (sport or "").strip().lower()
    if key:
        for profile in _PROFILES:
            if key in (h.lower() for h in profile.handles):
                return profile()
    return GenericProfile()


__all__ = ["SportProfile", "get_profile", "available_sports"]
