"""Tests for id -> name resolution."""

from __future__ import annotations

from storybuilder.resolve import Resolver, build_player_map, build_team_map


def test_build_team_map_uses_position():
    contestants = [
        {"id": "A", "name": "Alpha", "code": "ALP", "position": "away"},
        {"id": "B", "name": "Beta", "code": "BET", "position": "home"},
    ]
    teams = build_team_map(contestants)
    assert teams["B"].home is True
    assert teams["A"].home is False


def test_build_team_map_falls_back_to_order():
    contestants = [{"id": "A", "name": "Alpha"}, {"id": "B", "name": "Beta"}]
    teams = build_team_map(contestants)
    assert teams["A"].home is True
    assert teams["B"].home is False


def test_build_player_map_prefers_matchname():
    doc = {"squad": [{"person": [
        {"id": "p1", "matchName": "J. Kenny", "firstName": "Johnny", "lastName": "Kenny"},
        {"id": "p2", "firstName": "Kieran", "lastName": "Tierney"},
    ]}]}
    players = build_player_map([doc])
    assert players["p1"] == "J. Kenny"
    assert players["p2"] == "Kieran Tierney"


def test_resolver_falls_back_to_id_when_unknown():
    r = Resolver({}, {"p1": "J. Kenny"})
    assert r.player("p1") == "J. Kenny"
    assert r.player("unknown") == "unknown"
    assert r.player(None) is None
    assert r.team(None) is None
