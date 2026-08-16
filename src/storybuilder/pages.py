"""Typed, self-describing Story pages + a registry.

Each page type is a small dataclass that knows (a) how to serialize itself to the
output dict (`to_dict`, omitting empty optional fields) and (b) its own JSON
Schema fragment (`SCHEMA`). Registering them in ``PAGE_TYPES`` gives a single
source of truth: the output schema's page branches are derived from the same
fragments (see ``page_schemas``/``build_pages_schema``), and a test asserts every
registered type has a matching branch, so builder/schema/viewer can't silently
drift. Adding a page type = add a dataclass here + a renderer in the viewer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

_STR = {"type": "string"}
_INT = {"type": "integer"}


@dataclass(frozen=True)
class CoverPage:
    TYPE = "cover"
    SCHEMA = {
        "type": "object",
        "required": ["type", "headline", "image"],
        "additionalProperties": True,
        "properties": {
            "type": {"const": "cover"},
            "headline": _STR,
            "subheadline": _STR,
            "image": _STR,
        },
    }

    headline: str
    image: str
    subheadline: str = ""

    def to_dict(self) -> dict:
        page: dict = {"type": self.TYPE, "headline": self.headline, "image": self.image}
        if self.subheadline:
            page["subheadline"] = self.subheadline
        return page


@dataclass(frozen=True)
class HighlightPage:
    TYPE = "highlight"
    SCHEMA = {
        "type": "object",
        "required": ["type", "minute", "headline", "caption"],
        "additionalProperties": True,
        "properties": {
            "type": {"const": "highlight"},
            "minute": {"type": "integer", "minimum": 0, "maximum": 130},
            "headline": _STR,
            "caption": _STR,
            "image": _STR,
            "explanation": _STR,
        },
    }

    minute: int
    headline: str
    caption: str
    image: str = ""
    explanation: str = ""

    def to_dict(self) -> dict:
        page: dict = {
            "type": self.TYPE,
            "minute": self.minute,
            "headline": self.headline,
            "caption": self.caption,
        }
        if self.image:
            page["image"] = self.image
        if self.explanation:
            page["explanation"] = self.explanation
        return page


@dataclass(frozen=True)
class InfoPage:
    """A generic free-text page (e.g. a narrative beat)."""

    TYPE = "info"
    SCHEMA = {
        "type": "object",
        "required": ["type", "headline"],
        "additionalProperties": True,
        "properties": {
            "type": {"const": "info"},
            "headline": _STR,
            "body": _STR,
        },
    }

    headline: str
    body: str = ""

    def to_dict(self) -> dict:
        page: dict = {"type": self.TYPE, "headline": self.headline}
        if self.body:
            page["body"] = self.body
        return page


@dataclass(frozen=True)
class SummaryPage:
    """The full-time scoreboard + home-vs-away stat comparison."""

    TYPE = "summary"
    SCHEMA = {
        "type": "object",
        "required": [
            "type",
            "headline",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "stats",
        ],
        "additionalProperties": True,
        "properties": {
            "type": {"const": "summary"},
            "headline": _STR,
            "home_team": _STR,
            "away_team": _STR,
            "home_code": _STR,
            "away_code": _STR,
            "home_score": _INT,
            "away_score": _INT,
            "stats": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["label", "home", "away"],
                    "additionalProperties": True,
                    "properties": {"label": _STR, "home": _INT, "away": _INT},
                },
            },
            "body": _STR,
        },
    }

    home_team: str
    away_team: str
    home_score: int
    away_score: int
    home_code: str = ""
    away_code: str = ""
    headline: str = "Full time"
    stats: list[dict] = field(default_factory=list)
    body: str = ""

    def to_dict(self) -> dict:
        page: dict = {
            "type": self.TYPE,
            "headline": self.headline,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_code": self.home_code or "HOME",
            "away_code": self.away_code or "AWAY",
            "home_score": self.home_score,
            "away_score": self.away_score,
            "stats": list(self.stats),
        }
        if self.body:
            page["body"] = self.body
        return page


#: All known page types, keyed by their ``type`` discriminator.
PAGE_TYPES: dict[str, type] = {cls.TYPE: cls for cls in (CoverPage, HighlightPage, InfoPage, SummaryPage)}


def page_schemas() -> list[dict]:
    """The JSON Schema fragment for every registered page type."""
    return [cls.SCHEMA for cls in PAGE_TYPES.values()]


def build_pages_schema() -> dict:
    """The ``pages`` array schema (``anyOf`` over every page type)."""
    return {"type": "array", "minItems": 1, "items": {"anyOf": page_schemas()}}
