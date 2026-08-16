"""Typed pages: serialization round-trips and schema/registry coverage.

These guard the builder<->schema<->viewer contract: every registered page type
must have a matching branch in the shipped JSON Schema (keyed by its `type`
const), so the three can't silently drift apart.
"""

from __future__ import annotations

import json

from conftest import SCHEMA_PATH
from storybuilder.pages import (
    PAGE_TYPES,
    CoverPage,
    HighlightPage,
    InfoPage,
    SummaryPage,
    build_pages_schema,
)


def _schema_type_consts() -> set[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    branches = schema["properties"]["pages"]["items"]["anyOf"]
    return {b["properties"]["type"]["const"] for b in branches}


def test_every_registered_page_type_has_a_schema_branch():
    assert set(PAGE_TYPES) <= _schema_type_consts()


def test_registry_and_schema_are_in_sync():
    # Exact parity: no orphan schema branch, no unregistered page type.
    assert set(PAGE_TYPES) == _schema_type_consts()


def test_build_pages_schema_matches_registry():
    built = build_pages_schema()
    consts = {b["properties"]["type"]["const"] for b in built["items"]["anyOf"]}
    assert consts == set(PAGE_TYPES)


def test_cover_omits_empty_subheadline():
    assert CoverPage(headline="A vs B", image="x.jpg").to_dict() == {
        "type": "cover",
        "headline": "A vs B",
        "image": "x.jpg",
    }
    assert CoverPage("A", "x.jpg", subheadline="sub").to_dict()["subheadline"] == "sub"


def test_highlight_omits_empty_optionals():
    page = HighlightPage(minute=9, headline="GOAL", caption="c").to_dict()
    assert page == {"type": "highlight", "minute": 9, "headline": "GOAL", "caption": "c"}
    full = HighlightPage(9, "GOAL", "c", image="i.jpg", explanation="why").to_dict()
    assert full["image"] == "i.jpg" and full["explanation"] == "why"


def test_info_omits_empty_body():
    assert InfoPage(headline="H").to_dict() == {"type": "info", "headline": "H"}


def test_summary_defaults_codes_and_always_emits_stats():
    page = SummaryPage(home_team="Celtic", away_team="Killie", home_score=4, away_score=0).to_dict()
    assert page["type"] == "summary"
    assert page["home_code"] == "HOME" and page["away_code"] == "AWAY"
    assert page["stats"] == []
    assert "body" not in page
