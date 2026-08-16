"""Proves adding a new sport is trivial: the declarative BasketballProfile is
auto-discovered and produces a valid, correctly-scored Story with no changes to
the core, the registry, or the viewer."""

from __future__ import annotations

from conftest import REPO_ROOT, make_basketball_feed
from storybuilder.adapters import get_adapter
from storybuilder.assets import Assets
from storybuilder.profiles import available_sports, get_profile
from storybuilder.profiles.basketball import BasketballProfile
from storybuilder.story import build_story
from storybuilder.validate import validate_story


def _build(feed):
    match = get_adapter(feed).parse(feed, [], source="feed.json")
    profile = get_profile(match.sport)
    return build_story(match, profile, Assets(REPO_ROOT / "assets")), profile


def test_basketball_is_auto_registered():
    assert "basketball" in available_sports()
    assert isinstance(get_profile("Basketball"), BasketballProfile)


def test_basketball_scoring_from_declarative_config():
    story, profile = _build(make_basketball_feed())
    assert isinstance(profile, BasketballProfile)
    # Home: 2 (layup) + 2 (dunk) + 2 (buzzer beater) = 6; Away: 2 + 3 = 5.
    fs = story["metrics"]["final_score"]
    assert (fs["home"], fs["away"]) == (6, 5)


def test_basketball_story_validates_and_reads_well(schema):
    story, _ = _build(make_basketball_feed())
    assert validate_story(story, schema) == []
    assert story["pages"][0]["type"] == "cover"
    assert "Hawks 6-5 Wolves" == story["pages"][0]["headline"]
    # Declarative `terms` drive the headline labels.
    headlines = " ".join(p.get("headline", "") for p in story["pages"])
    assert "DUNK" in headlines and "BUZZER BEATER" in headlines


def test_must_include_events_present():
    story, _ = _build(make_basketball_feed())
    headlines = " ".join(p.get("headline", "") for p in story["pages"] if p["type"] == "highlight")
    assert "DUNK" in headlines and "BUZZER BEATER" in headlines
