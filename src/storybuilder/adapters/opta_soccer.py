"""Adapter for the Opta-style commentary feed used in this task.

Format quirks this adapter absorbs so nothing downstream has to care:
- events live under ``messages[<lang>].message`` (a list)
- events are stored newest-first; we re-sort ascending
- ``minute`` / ``period`` / ``second`` arrive as strings
- ``period`` ``14`` is a synthetic "match end" marker, not a real half
- teams/players are referenced by opaque ids (resolved via metadata + squads)
- some events omit ``playerRef1``
"""

from __future__ import annotations

from ..models import Event, Match
from ..resolve import Resolver, build_player_map, build_team_map
from .base import FeedAdapter

#: ``period`` values that are bookkeeping markers rather than real play periods.
SYNTHETIC_PERIODS = {"14", "16"}


class OptaSoccerAdapter(FeedAdapter):
    name = "opta-soccer"

    @classmethod
    def can_parse(cls, raw: dict) -> bool:
        return "matchInfo" in raw and "messages" in raw

    def parse(self, raw: dict, squads: list[dict], *, source: str = "") -> Match:
        info = raw.get("matchInfo", {})
        contestants = info.get("contestant", []) or []
        team_map = build_team_map(contestants)
        resolver = Resolver(team_map, build_player_map(squads))

        home = next((t for t in team_map.values() if t.home), None)
        away = next((t for t in team_map.values() if not t.home), None)
        # Fall back to declaration order if positions were absent.
        ordered = list(team_map.values())
        if home is None and ordered:
            home = ordered[0]
        if away is None and len(ordered) > 1:
            away = ordered[1]

        events = self._parse_events(raw.get("messages", []), resolver)

        return Match(
            home=home,
            away=away,
            events=events,
            sport=self._sport_name(info),
            competition=self._competition_name(info),
            venue=(info.get("venue") or {}).get("longName", ""),
            date=info.get("localDate") or info.get("date", ""),
            source=source,
            match_id=info.get("id", ""),
        )

    def _parse_events(self, messages: list[dict], resolver: Resolver) -> list[Event]:
        raw_events = self._select_messages(messages)
        events: list[Event] = []
        seen: set[str] = set()
        for m in raw_events:
            period = str(m.get("period", "")).strip()
            if period in SYNTHETIC_PERIODS:
                continue
            event = Event(
                type=(m.get("type") or "").strip(),
                period=_to_int(period),
                minute=_to_int(m.get("minute")),
                second=_to_int(m.get("second")),
                team=resolver.team(m.get("teamRef1")),
                player=resolver.player(m.get("playerRef1")),
                player2=resolver.player(m.get("playerRef2")),
                comment=(m.get("comment") or "").strip(),
                raw_id=str(m.get("id", "")),
            )
            dedupe_key = event.raw_id or f"{event.sort_key}-{event.type}-{event.comment}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            events.append(event)

        # Stored newest-first; re-sort ascending. Python's sort is stable, so
        # events sharing a timestamp keep their (reversed) feed order relative
        # to each other - which we correct by reversing first.
        events.reverse()
        events.sort(key=lambda e: e.sort_key)
        return events

    @staticmethod
    def _select_messages(messages: list[dict]) -> list[dict]:
        if not messages:
            return []
        # Prefer English commentary when multiple languages are present.
        chosen = next(
            (block for block in messages if str(block.get("language", "")).startswith("en")),
            messages[0],
        )
        return chosen.get("message", []) or []

    @staticmethod
    def _sport_name(info: dict) -> str:
        return (info.get("sport") or {}).get("name", "")

    @staticmethod
    def _competition_name(info: dict) -> str:
        comp = info.get("competition") or {}
        return comp.get("knownName") or comp.get("name", "")


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default
