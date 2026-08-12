"""End-to-end invariants on the assembled Story (soccer + generic fallback)."""

from __future__ import annotations

from storybuilder.adapters import get_adapter
from storybuilder.assets import Assets
from storybuilder.profiles import get_profile
from storybuilder.story import build_story
from storybuilder.validate import validate_story

from conftest import REPO_ROOT, make_generic_feed


def _build(feed, squads):
    match = get_adapter(feed).parse(feed, squads, source="feed.json")
    profile = get_profile(match.sport)
    assets = Assets(REPO_ROOT / "assets")
    return build_story(match, profile, assets)


def test_soccer_story_validates(sample_feed, squads, schema):
    story = _build(sample_feed, squads)
    assert validate_story(story, schema) == []


def test_first_page_is_cover(sample_feed, squads):
    story = _build(sample_feed, squads)
    assert story["pages"][0]["type"] == "cover"
    assert story["pages"][0]["image"]


def test_highlights_have_required_fields(sample_feed, squads):
    story = _build(sample_feed, squads)
    highlights = [p for p in story["pages"] if p["type"] == "highlight"]
    assert highlights
    for p in highlights:
        assert isinstance(p["minute"], int)
        assert p["headline"] and p["caption"]


def test_highlight_minutes_non_decreasing(sample_feed, squads):
    story = _build(sample_feed, squads)
    minutes = [p["minute"] for p in story["pages"] if p["type"] == "highlight"]
    assert minutes == sorted(minutes)


def test_cover_reflects_actual_teams_and_score(sample_feed, squads):
    story = _build(sample_feed, squads)
    assert story["pages"][0]["headline"] == "Celtic 4-0 Kilmarnock"


# --- genericity: different teams + a non-soccer sport ---------------------
def test_generic_feed_produces_valid_story(schema):
    story = _build(make_generic_feed(), [])
    assert validate_story(story, schema) == []
    assert story["pages"][0]["type"] == "cover"
    # Different teams, no soccer assumptions.
    assert "Sharks" in story["title"] and "Eagles" in story["title"]


def test_generic_feed_uses_generic_profile_no_scoring(schema):
    story = _build(make_generic_feed(), [])
    # Generic profile is score-agnostic: cover is a "vs" headline, not a scoreline.
    assert "vs" in story["pages"][0]["headline"]
