"""Tests for the reusable orchestration entry point (`app.build_story_from_feed`)."""

from __future__ import annotations

import pytest

from conftest import REPO_ROOT, make_basketball_feed, make_generic_feed
from storybuilder.app import StoryValidationError, build_story_from_feed, validate_story_dict

ASSETS = str(REPO_ROOT / "assets")


def test_build_from_feed_matches_cli_pipeline(sample_feed, squads):
    story = build_story_from_feed(sample_feed, squads, assets_dir=ASSETS, source="match_events.json")
    assert story["pages"][0]["type"] == "cover"
    assert story["pages"][-1]["type"] == "summary"
    assert story["pages"][0]["headline"] == "Celtic 4-0 Kilmarnock"
    assert validate_story_dict(story) == []


def test_build_from_feed_validates_by_default(sample_feed, squads):
    # Should not raise; the sample builds a schema-valid Story.
    build_story_from_feed(sample_feed, squads, assets_dir=ASSETS)


def test_sport_override_forces_generic(sample_feed, squads):
    story = build_story_from_feed(sample_feed, squads, sport="generic-not-a-sport", assets_dir=ASSETS)
    # Unknown sport => generic fallback => no summary page, "vs" cover.
    assert "vs" in story["pages"][0]["headline"]
    assert all(p["type"] != "summary" for p in story["pages"])


def test_basketball_and_generic_feeds_build(schema):
    for feed in (make_basketball_feed(), make_generic_feed()):
        story = build_story_from_feed(feed, assets_dir=ASSETS)
        assert story["pages"][0]["type"] == "cover"


def test_story_id_is_passed_through(sample_feed, squads):
    story = build_story_from_feed(sample_feed, squads, story_id="fixed-id", assets_dir=ASSETS)
    assert story["story_id"] == "fixed-id"


def test_validation_error_is_raised(sample_feed, squads, tmp_path):
    # A schema that requires an impossible field makes validation fail loudly.
    bad_schema = tmp_path / "bad.json"
    bad_schema.write_text('{"type": "object", "required": ["nope"]}', encoding="utf-8")
    with pytest.raises(StoryValidationError) as exc:
        build_story_from_feed(sample_feed, squads, assets_dir=ASSETS, schema_path=str(bad_schema))
    assert exc.value.errors


def test_unknown_format_raises_value_error(sample_feed):
    with pytest.raises(ValueError):
        build_story_from_feed(sample_feed, fmt="does-not-exist", assets_dir=ASSETS)
