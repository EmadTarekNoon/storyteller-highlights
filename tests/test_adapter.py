"""Tests for the Opta soccer adapter: normalization, ordering, resolution."""

from __future__ import annotations

from storybuilder.adapters import get_adapter
from storybuilder.adapters.opta_soccer import OptaSoccerAdapter


def parse(feed, squads):
    return get_adapter(feed).parse(feed, squads, source="match_events.json")


def test_autodetects_opta_adapter(sample_feed):
    assert isinstance(get_adapter(sample_feed), OptaSoccerAdapter)


def test_teams_and_metadata_resolved(sample_feed, squads):
    match = parse(sample_feed, squads)
    assert match.home.name == "Celtic" and match.home.home is True
    assert match.away.name == "Kilmarnock" and match.away.home is False
    assert match.sport.lower() == "soccer"
    assert match.venue == "Celtic Park"


def test_events_sorted_ascending(sample_feed, squads):
    match = parse(sample_feed, squads)
    keys = [e.sort_key for e in match.events]
    assert keys == sorted(keys), "events must be chronological"


def test_synthetic_end_period_dropped(sample_feed, squads):
    match = parse(sample_feed, squads)
    # period 14 markers must be filtered out
    assert all(e.period not in (14, 16) for e in match.events)


def test_minute_period_second_are_ints(sample_feed, squads):
    match = parse(sample_feed, squads)
    e = match.events[0]
    assert isinstance(e.minute, int) and isinstance(e.period, int) and isinstance(e.second, int)


def test_player_ids_resolved_to_names(sample_feed, squads):
    match = parse(sample_feed, squads)
    goals = [e for e in match.events if e.type in ("goal", "penalty goal")]
    assert goals, "sample has goals"
    # No resolved player should still look like a raw 25-char opta id.
    for g in goals:
        assert g.player and not (len(g.player) == 25 and g.player.isalnum())


def test_missing_playerref_is_tolerated(sample_feed, squads):
    match = parse(sample_feed, squads)  # must not raise
    assert any(e.player is None for e in match.events)
