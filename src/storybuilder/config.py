"""Externalized, data-driven profile configuration.

Sport behaviour (ranking weights, must-include rules, scoring, caption terms,
summary rows, …) can live in ``config/<sport>.json`` instead of Python, so it can
be retuned without code changes (A/B heuristics, per-customer branding, …). A
matching file is applied on top of a profile's declarative class defaults; when
absent, the built-in defaults are used unchanged.

Only a known allow-list of keys is applied, and list values for the ``*_types``
fields are normalized to frozensets / ``StatRow`` tuples to match the shapes the
behaviour collaborators expect.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import StatRow

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_DIR = _REPO_ROOT / "config"

#: Config keys that map directly onto ``SportProfile`` attributes.
_ALLOWED_KEYS = frozenset(
    {
        "target_highlights",
        "default_weight",
        "weights",
        "scoring",
        "must_include_types",
        "own_types",
        "terms",
        "noise_types",
        "score_label",
        "summary_stats",
    }
)

#: Keys whose JSON arrays become frozensets of strings.
_SET_KEYS = frozenset({"must_include_types", "own_types", "noise_types"})


def load_config(sport: str, config_dir: str | Path) -> dict | None:
    """Return the parsed config for ``sport`` from ``config_dir``, or ``None``."""
    if not sport:
        return None
    path = Path(config_dir) / f"{sport.strip().lower()}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_config(raw: dict) -> dict:
    """Coerce a raw config dict into the attribute shapes profiles expect."""
    cfg: dict = {}
    for key, value in raw.items():
        if key not in _ALLOWED_KEYS or value is None:
            continue
        if key in _SET_KEYS:
            cfg[key] = frozenset(value)
        elif key == "weights":
            cfg[key] = {k: float(v) for k, v in value.items()}
        elif key == "summary_stats":
            cfg[key] = tuple(
                StatRow(
                    label=row["label"],
                    types=frozenset(row["types"]),
                    attribute=row.get("attribute", "acting"),
                )
                for row in value
            )
        else:
            cfg[key] = value
    return cfg


def apply_config(profile, raw: dict) -> None:
    """Apply a raw config onto a profile *instance* (overriding class defaults)."""
    for key, value in normalize_config(raw).items():
        setattr(profile, key, value)
