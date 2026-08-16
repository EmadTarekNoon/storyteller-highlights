"""Validate an assembled Story against ``schema/story.schema.json``.

Schema quirk we work around: the schema's top-level ``required`` lists
``pack_id`` while its ``properties`` only define ``story_id`` *and*
``additionalProperties`` is ``false``. As written the schema is unsatisfiable -
no document can both provide ``pack_id`` (required) and avoid it (forbidden by
``additionalProperties: false``). We interpret the intent as ``story_id`` (which
matches the defined properties, both READMEs and the invariants) and reconcile
the *schema* by mapping ``pack_id`` -> ``story_id`` in ``required`` before
validating. See DECISIONS.md.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.validators import validator_for


def load_schema(schema_path: str | Path) -> dict:
    return json.loads(Path(schema_path).read_text(encoding="utf-8"))


def validate_story(story: dict, schema: dict) -> list[str]:
    """Return a list of human-readable validation errors (empty == valid)."""

    effective = _reconcile_schema(schema)
    cls = validator_for(effective, default=Draft202012Validator)
    validator = cls(effective, format_checker=cls.FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(story), key=lambda e: list(e.path))
    return [_format_error(e) for e in errors]


def _reconcile_schema(schema: dict) -> dict:
    """Return a satisfiable copy: ``pack_id`` in ``required`` becomes ``story_id``."""

    required = schema.get("required", [])
    if "pack_id" not in required:
        return schema
    fixed = dict(schema)
    fixed["required"] = ["story_id" if key == "pack_id" else key for key in required]
    return fixed


def _format_error(error) -> str:
    location = "/".join(str(p) for p in error.path) or "<root>"
    return f"{location}: {error.message}"
