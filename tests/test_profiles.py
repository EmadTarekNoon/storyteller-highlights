"""Tests for profile selection, soccer scoring/ranking and captions."""

from __future__ import annotations

from storybuilder.adapters import get_adapter
from storybuilder.models import Event, Match, Score, Team
from storybuilder.pipeline import final_score, select_highlights
from storybuilder.profiles import get_profile
from storybuilder.profiles.generic import GenericProfile
from storybuilder.profiles.soccer import SoccerProfile


def _match(sample_feed, squads) -> Match:
    return get_adapter(sample_feed).parse(sample_feed, squads)


def test_registry_selects_soccer_and_generic():
    assert isinstance(get_profile("Soccer"), SoccerProfile)
    assert isinstance(get_profile("football"), SoccerProfile)
    assert isinstance(get_profile("Rugby"), GenericProfile)
    assert isinstance(get_profile(None), GenericProfile)


def test_soccer_final_score_matches_reality(sample_feed, squads):
    match = _match(sample_feed, squads)
    final = final_score(match, SoccerProfile())
    assert (final.home, final.away) == (4, 0)


def test_all_goals_are_highlighted(sample_feed, squads):
    match = _match(sample_feed, squads)
    ranked = select_highlights(match, SoccerProfile())
    goal_types = {"goal", "penalty goal"}
    n_goal_events = sum(1 for e in match.events if e.type in goal_types)
    n_goal_highlights = sum(1 for r in ranked if r.event.type in goal_types)
    assert n_goal_highlights == n_goal_events == 4


def test_running_score_is_monotonic(sample_feed, squads):
    match = _match(sample_feed, squads)
    ranked = select_highlights(match, SoccerProfile())
    totals = [r.score.home + r.score.away for r in ranked]
    assert totals == sorted(totals), "running score must never decrease"


def test_goal_caption_has_minute_player_and_score():
    profile = SoccerProfile()
    home = Team(id="H", name="Celtic", home=True)
    away = Team(id="A", name="Kilmarnock", home=False)
    match = Match(home=home, away=away, events=[], sport="Soccer")
    event = Event(
        type="goal",
        period=1,
        minute=9,
        second=0,
        team=home,
        player="J. Kenny",
        comment="Goal! Celtic 1, Kilmarnock 0. Johnny Kenny (Celtic) left footed shot.",
    )
    cap = profile.caption(event, Score(home=1, away=0), match)
    assert "9'" in cap.headline
    assert "1-0" in cap.headline
    assert "Kenny" in cap.caption
    assert "Celtic 1-0 Kilmarnock" in cap.caption


def test_own_goal_credits_opponent():
    profile = SoccerProfile()
    home = Team(id="H", name="Home", home=True)
    away = Team(id="A", name="Away", home=False)
    match = Match(home=home, away=away, events=[], sport="Soccer")
    og = Event(type="own goal", period=1, minute=5, second=0, team=home)
    delta = profile.score_delta(og, match)
    assert (delta.home, delta.away) == (0, 1)
