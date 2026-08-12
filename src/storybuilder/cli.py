"""Command-line entry point.

Wires the pluggable pieces together:
    load feed -> adapter -> profile -> build Story -> validate -> write JSON.

Example:
    python -m storybuilder --in data/match_events.json \\
        --squads data/celtic-squad.json data/kilmarnock-squad.json \\
        --out out/story.json --pretty
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters import available_formats, get_adapter
from .assets import Assets
from .profiles import available_sports, get_profile
from .story import build_story
from .validate import load_schema, validate_story

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SCHEMA = _REPO_ROOT / "schema" / "story.schema.json"
_DEFAULT_ASSETS = "assets"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="storybuilder",
        description="Turn sports match events into a Story (JSON bundle of Pages).",
    )
    p.add_argument("--in", dest="input", required=True, help="Path to the match events feed (JSON).")
    p.add_argument("--out", dest="output", default="out/story.json", help="Where to write the Story JSON.")
    p.add_argument("--squads", nargs="*", default=[], help="Optional squad JSON files for id->name resolution.")
    p.add_argument("--format", dest="fmt", default=None,
                   help=f"Feed format (default: auto-detect). One of: {', '.join(available_formats())}.")
    p.add_argument("--sport", default=None,
                   help=f"Override sport profile. Known: {', '.join(available_sports())} (else generic).")
    p.add_argument("--assets", default=_DEFAULT_ASSETS, help="Assets directory used for page images.")
    p.add_argument("--schema", default=str(_DEFAULT_SCHEMA), help="Path to the Story JSON Schema.")
    p.add_argument("--story-id", default=None, help="Explicit story_id (default: generated).")
    p.add_argument("--pretty", action="store_true", help="Pretty-print the output JSON.")
    p.add_argument("--no-validate", action="store_true", help="Skip schema validation.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    squads = [json.loads(Path(s).read_text(encoding="utf-8")) for s in args.squads]

    adapter = get_adapter(raw, args.fmt)
    match = adapter.parse(raw, squads, source=Path(args.input).name)

    profile = get_profile(args.sport or match.sport)
    assets = Assets(args.assets)

    story = build_story(match, profile, assets, story_id=args.story_id)

    if not args.no_validate:
        errors = validate_story(story, load_schema(args.schema))
        if errors:
            print("Story failed schema validation:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            return 1

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if args.pretty else None
    out_path.write_text(
        json.dumps(story, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(
        f"Wrote {out_path} - {len(story['pages'])} pages "
        f"(sport: {profile.__class__.__name__}, format: {adapter.name})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
