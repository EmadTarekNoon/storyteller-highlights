"""Basketball profile — a worked example of how little a new sport needs.

The entire sport is expressed with declarative class attributes; the base class
supplies scoring, ranking, captions, cover, info page and metrics. Drop this
file in the package and it is auto-registered (no registry edits).
"""

from __future__ import annotations

from ..models import StatRow
from .base import SportProfile


class BasketballProfile(SportProfile):
    handles = ("basketball",)
    target_highlights = 12

    # Points each scoring event adds to the acting team.
    scoring = {"3 points": 3, "2 points": 2, "free throw": 1, "dunk": 2, "buzzer beater": 2}

    # Ranking importance (unlisted types fall back to default_weight).
    weights = {
        "buzzer beater": 100,
        "dunk": 80,
        "3 points": 60,
        "2 points": 40,
        "block": 45,
        "steal": 35,
        "free throw": 20,
        "foul": 15,
        "timeout": 5,
    }

    must_include_types = frozenset({"buzzer beater", "dunk"})

    # Headline labels.
    terms = {
        "3 points": "THREE",
        "2 points": "BUCKET",
        "free throw": "FREE THROW",
        "dunk": "DUNK",
        "buzzer beater": "BUZZER BEATER",
    }

    # Full-time summary: score row is labelled "Points"; these rows render as
    # the same home-vs-away comparison bars soccer uses.
    score_label = "Points"
    summary_stats = (
        StatRow("3-pointers", frozenset({"3 points"})),
        StatRow("Dunks", frozenset({"dunk"})),
        StatRow("Free throws", frozenset({"free throw"})),
        StatRow("Blocks", frozenset({"block"})),
        StatRow("Steals", frozenset({"steal"})),
        StatRow("Fouls", frozenset({"foul"})),
    )
