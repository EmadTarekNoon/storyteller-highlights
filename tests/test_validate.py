"""Tests for schema validation, including the pack_id/story_id reconciliation."""

from __future__ import annotations

from storybuilder.validate import validate_story


def _valid_story() -> dict:
    return {
        "story_id": "s1",
        "title": "A vs B",
        "source": "feed.json",
        "created_at": "2025-01-01T00:00:00Z",
        "pages": [{"type": "cover", "headline": "A 1-0 B", "image": "assets/x.jpg"}],
    }


def test_story_id_satisfies_pack_id_requirement(schema):
    # Even though the schema's `required` lists pack_id, a story_id-only doc
    # validates thanks to schema reconciliation.
    assert validate_story(_valid_story(), schema) == []


def test_missing_required_field_reports_error(schema):
    story = _valid_story()
    del story["title"]
    errors = validate_story(story, schema)
    assert any("title" in e for e in errors)


def test_bad_created_at_format_is_caught(schema):
    story = _valid_story()
    story["created_at"] = "not-a-date"
    errors = validate_story(story, schema)
    assert errors, "invalid date-time should fail format validation"


def test_empty_pages_rejected(schema):
    story = _valid_story()
    story["pages"] = []
    assert validate_story(story, schema)
