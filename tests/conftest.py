"""Shared fixtures and helpers for the test suite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
SCHEMA_PATH = REPO_ROOT / "schema" / "story.schema.json"


@pytest.fixture(scope="session")
def sample_feed() -> dict:
    return json.loads((DATA_DIR / "match_events.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def squads() -> list[dict]:
    return [
        json.loads((DATA_DIR / "celtic-squad.json").read_text(encoding="utf-8")),
        json.loads((DATA_DIR / "kilmarnock-squad.json").read_text(encoding="utf-8")),
    ]


@pytest.fixture(scope="session")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def make_generic_feed() -> dict:
    """A tiny synthetic feed for two *different* teams and a *non-soccer* sport.

    Used to prove the pipeline is generic: no soccer/team assumptions leak into
    the core, and an unknown sport still yields a valid Story via the fallback
    profile.
    """
    return {
        "matchInfo": {
            "id": "synthetic-1",
            "localDate": "2025-01-01",
            "sport": {"name": "Rugby"},
            "competition": {"name": "Test Cup"},
            "venue": {"longName": "Test Arena"},
            "contestant": [
                {"id": "T1", "name": "Sharks", "code": "SHK", "position": "home"},
                {"id": "T2", "name": "Eagles", "code": "EGL", "position": "away"},
            ],
        },
        "messages": [
            {
                "language": "en-gb",
                "message": [
                    # newest-first, like the real feed
                    {"id": "9", "type": "try", "period": "2", "minute": "70", "second": "0",
                     "teamRef1": "T1", "comment": "Try scored by the Sharks."},
                    {"id": "8", "type": "penalty", "period": "2", "minute": "55", "second": "0",
                     "teamRef1": "T2", "comment": "Penalty kick for the Eagles."},
                    {"id": "7", "type": "card", "period": "1", "minute": "30", "second": "0",
                     "teamRef1": "T1", "comment": "Yellow card shown."},
                    {"id": "6", "type": "knock on", "period": "1", "minute": "12", "second": "0",
                     "teamRef1": "T2", "comment": "Knock on."},
                    {"id": "5", "type": "kickoff", "period": "1", "minute": "0", "second": "0",
                     "teamRef1": "T1", "comment": "Match begins."},
                ],
            }
        ],
    }
