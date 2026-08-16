"""Externalized config: loading, override behaviour, and default parity."""

from __future__ import annotations

import json

from conftest import REPO_ROOT
from storybuilder.adapters import get_adapter
from storybuilder.assets import Assets
from storybuilder.config import apply_config, load_config, normalize_config
from storybuilder.models import Event
from storybuilder.profiles import get_profile
from storybuilder.profiles.soccer import WEIGHTS, SoccerProfile
from storybuilder.story import build_story

ASSETS = REPO_ROOT / "assets"
CONFIG_DIR = REPO_ROOT / "config"


def _ev(t: str) -> Event:
    return Event(type=t, period=1, minute=1, second=0)


def test_shipped_soccer_config_loads():
    raw = load_config("soccer", CONFIG_DIR)
    assert raw is not None and raw["score_label"] == "Goals"


def test_config_is_applied_via_get_profile():
    profile = get_profile("soccer", config_dir=str(CONFIG_DIR))
    # weight() is driven by the externalized weights map.
    assert profile.weight(_ev("goal")) == WEIGHTS["goal"]
    assert profile.must_include(_ev("red card")) is True


def test_shipped_config_matches_builtin_defaults():
    """The shipped soccer.json must reproduce the hardcoded SoccerProfile."""
    configured = get_profile("soccer", config_dir=str(CONFIG_DIR))
    builtin = SoccerProfile()
    for t in ["goal", "corner", "offside", "free kick lost", "unseen-type"]:
        assert configured.weight(_ev(t)) == builtin.weight(_ev(t))
    assert configured.must_include_types == builtin.must_include_types
    assert configured.scoring == builtin.scoring
    assert configured.summary_stats == builtin.summary_stats


def test_full_story_parity_with_and_without_config(sample_feed, squads):
    match = get_adapter(sample_feed).parse(sample_feed, squads)
    assets = Assets(ASSETS)
    configured = build_story(match, get_profile("soccer", config_dir=str(CONFIG_DIR)), assets)
    builtin = build_story(match, SoccerProfile(), assets)
    assert configured["pages"] == builtin["pages"]


def test_custom_config_dir_overrides_behaviour(tmp_path):
    (tmp_path / "soccer.json").write_text(
        json.dumps({"weights": {"corner": 999}, "must_include_types": ["corner"]}),
        encoding="utf-8",
    )
    profile = get_profile("soccer", config_dir=str(tmp_path))
    assert profile.weight(_ev("corner")) == 999.0
    assert profile.must_include(_ev("corner")) is True
    # A type not mentioned in the override falls back to the default weight.
    assert profile.weight(_ev("anything")) == profile.default_weight


def test_normalize_ignores_unknown_keys_and_coerces_types():
    cfg = normalize_config({"score_label": "Points", "bogus": 1, "own_types": ["own goal"]})
    assert cfg == {"score_label": "Points", "own_types": frozenset({"own goal"})}


def test_apply_config_sets_instance_attributes():
    p = SoccerProfile()
    apply_config(p, {"target_highlights": 3})
    assert p.target_highlights == 3
