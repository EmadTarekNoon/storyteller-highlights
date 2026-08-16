"""Resolve opaque feed references (team / player ids) into human names.

Feeds reference teams and players by id. Team ids resolve from the match
metadata; player ids resolve from any number of squad files. Everything here is
generic across teams/competitions - no names are hardcoded - and every lookup
degrades gracefully (falling back to the id) so captions never surface a raw id
by accident.
"""

from __future__ import annotations

from .models import Team


class Resolver:
    """Bidirectional-ish lookups for team and player ids."""

    def __init__(self, teams: dict[str, Team], players: dict[str, str]):
        self._teams = teams
        self._players = players

    def team(self, team_id: str | None) -> Team | None:
        if not team_id:
            return None
        return self._teams.get(team_id)

    def player(self, player_id: str | None) -> str | None:
        if not player_id:
            return None
        return self._players.get(player_id, player_id)


def build_team_map(contestants: list[dict]) -> dict[str, Team]:
    """Build id -> Team from a feed's ``matchInfo.contestant`` list.

    ``position`` (``home``/``away``) is used when present; otherwise the first
    two contestants are treated as home then away.
    """

    teams: dict[str, Team] = {}
    for idx, c in enumerate(contestants):
        position = (c.get("position") or "").lower()
        home = position == "home" if position else idx == 0
        team = Team(
            id=c.get("id", ""),
            name=c.get("name") or c.get("shortName") or c.get("code") or "Unknown",
            code=c.get("code", ""),
            home=home,
        )
        if team.id:
            teams[team.id] = team
    return teams


def build_player_map(squads: list[dict]) -> dict[str, str]:
    """Build id -> display name from any number of squad documents.

    Accepts the Opta-style squad shape (``squad[].person[]``) and prefers the
    concise ``matchName``, falling back through first/last name combinations.
    """

    players: dict[str, str] = {}
    for doc in squads:
        for squad in _iter_squads(doc):
            for person in squad.get("person", []) or []:
                pid = person.get("id")
                if not pid:
                    continue
                players[pid] = _person_name(person)
    return players


def _iter_squads(doc: dict) -> list[dict]:
    squad = doc.get("squad")
    if isinstance(squad, list):
        return squad
    if isinstance(squad, dict):
        return [squad]
    # Some feeds nest a single squad document at the top level.
    if "person" in doc:
        return [doc]
    return []


def _person_name(person: dict) -> str:
    for key in ("matchName", "knownName"):
        val = person.get(key)
        if val:
            return val
    first = person.get("shortFirstName") or person.get("firstName") or ""
    last = person.get("shortLastName") or person.get("lastName") or ""
    full = f"{first} {last}".strip()
    return full or person.get("id", "")
