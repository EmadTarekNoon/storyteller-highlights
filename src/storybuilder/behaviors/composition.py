"""Composition seam: build the structural pages (cover / summary) and metrics.

``SummaryComposer`` is the default: a cover derived from the scoreline and a
full-time home-vs-away comparison built declaratively from a profile's
``summary_stats``. Score-agnostic sports (no ``scoring`` and no ``summary_stats``)
get no fabricated scoreboard.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import Event, Match, Score, StatRow
from ..pages import SummaryPage
from .common import side_of


@runtime_checkable
class PageComposer(Protocol):
    def cover(self, match: Match, final: Score) -> dict: ...
    def info_pages(self, match: Match, final: Score, events: list[Event]) -> list[dict]: ...
    def metrics(self, match: Match, final: Score, events: list[Event]) -> dict: ...


class SummaryComposer:
    def __init__(
        self,
        scoring: dict[str, int],
        score_label: str,
        summary_stats: tuple[StatRow, ...],
    ):
        self._scoring = scoring
        self._score_label = score_label
        self._summary_stats = summary_stats

    def cover(self, match: Match, final: Score) -> dict:
        home = match.home.name if match.home else "Home"
        away = match.away.name if match.away else "Away"
        subparts = [p for p in (match.sport, match.competition, match.venue, match.date) if p]
        if self._scoring and (final.home or final.away):
            headline = f"{home} {final.home}-{final.away} {away}"
        else:
            headline = f"{home} vs {away}"
        return {"headline": headline, "subheadline": " | ".join(subparts)}

    def info_pages(self, match: Match, final: Score, events: list[Event]) -> list[dict]:
        # Score-agnostic sports: don't fabricate a 0-0 scoreboard.
        if not self._scoring and not self._summary_stats:
            return []

        rows: list[dict] = []
        if self._scoring:
            rows.append({"label": self._score_label, "home": final.home, "away": final.away})
        for row in self._summary_stats:
            home = away = 0
            for e in events:
                if e.type not in row.types:
                    continue
                side = side_of(e, match)
                if row.attribute == "opponent":
                    side = {"home": "away", "away": "home"}.get(side, "")
                if side == "home":
                    home += 1
                elif side == "away":
                    away += 1
            rows.append({"label": row.label, "home": home, "away": away})

        body = "\n".join(f"{r['label']}: {r['home']} - {r['away']}" for r in rows)
        page = SummaryPage(
            home_team=match.home.name if match.home else "Home",
            away_team=match.away.name if match.away else "Away",
            home_code=(match.home.code if match.home else ""),
            away_code=(match.away.code if match.away else ""),
            home_score=final.home,
            away_score=final.away,
            stats=rows,
            body=body,
        )
        return [page.to_dict()]

    def metrics(self, match: Match, final: Score, events: list[Event]) -> dict:
        return {
            "final_score": {"home": final.home, "away": final.away},
            "total_events": len(events),
        }
