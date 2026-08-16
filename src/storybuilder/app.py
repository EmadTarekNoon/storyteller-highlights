"""Reusable orchestration: feed (dict) -> validated Story (dict).

This is the single programmatic entry point shared by the CLI and the HTTP
service. It does no file IO and takes/returns plain dicts, so it is trivial to
call from a web handler, a notebook, or a test.

    load feed -> adapter -> profile -> build Story -> (optionally) validate
"""

from __future__ import annotations

from pathlib import Path

from .adapters import get_adapter
from .assets import Assets
from .profiles import get_profile
from .story import build_story
from .validate import load_schema, validate_story

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = _REPO_ROOT / "schema" / "story.schema.json"
DEFAULT_ASSETS = "assets"


class StoryValidationError(ValueError):
    """Raised when a built Story fails schema validation."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Story failed schema validation:\n  - " + "\n  - ".join(errors))


def build_story_from_feed(
    raw: dict,
    squads: list[dict] | None = None,
    *,
    fmt: str | None = None,
    sport: str | None = None,
    assets_dir: str = DEFAULT_ASSETS,
    story_id: str | None = None,
    source: str = "",
    config_dir: str | None = None,
    validate: bool = True,
    schema_path: str | Path = DEFAULT_SCHEMA,
) -> dict:
    """Build a Story dict from an already-decoded feed.

    Raises :class:`StoryValidationError` when ``validate`` is true and the
    resulting Story does not satisfy the schema.
    """
    squads = squads or []
    adapter = get_adapter(raw, fmt)
    match = adapter.parse(raw, squads, source=source)

    profile = get_profile(sport or match.sport, config_dir=config_dir)
    assets = Assets(assets_dir)

    story = build_story(match, profile, assets, story_id=story_id)

    if validate:
        errors = validate_story_dict(story, schema_path)
        if errors:
            raise StoryValidationError(errors)
    return story


def validate_story_dict(story: dict, schema_path: str | Path = DEFAULT_SCHEMA) -> list[str]:
    """Validate a Story dict against the schema; returns error strings (empty == ok)."""
    return validate_story(story, load_schema(schema_path))
