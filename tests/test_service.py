"""Tests for the optional FastAPI service (skipped if the extra isn't installed)."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from conftest import make_basketball_feed  # noqa: E402
from storybuilder.service import create_app  # noqa: E402

client = TestClient(create_app())


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_post_stories_builds_a_valid_story():
    r = client.post("/stories", json={"feed": make_basketball_feed()})
    assert r.status_code == 200
    story = r.json()
    assert story["pages"][0]["type"] == "cover"
    assert story["pages"][-1]["type"] == "summary"
    assert story["pages"][0]["headline"] == "Hawks 6-5 Wolves"


def test_post_stories_unknown_format_is_400():
    r = client.post("/stories", json={"feed": make_basketball_feed(), "format": "nope"})
    assert r.status_code == 400


def test_post_stories_unrecognized_feed_is_400():
    r = client.post("/stories", json={"feed": {"not": "a feed"}})
    assert r.status_code == 400
