"""Command-line entry point.

A thin wrapper over :func:`storybuilder.app.build_story_from_feed`: it only does
argument parsing and file IO; all orchestration lives in ``app.py`` so the CLI
and the HTTP service share exactly the same logic.

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

from .adapters import available_formats
from .app import DEFAULT_ASSETS, DEFAULT_SCHEMA, StoryValidationError, build_story_from_feed
from .profiles import available_sports


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="storybuilder",
        description="Turn sports match events into a Story (JSON bundle of Pages).",
    )
    p.add_argument("--in", dest="input", required=True, help="Path to the match events feed (JSON).")
    p.add_argument("--out", dest="output", default="out/story.json", help="Where to write the Story JSON.")
    p.add_argument(
        "--squads", nargs="*", default=[], help="Optional squad JSON files for id->name resolution."
    )
    p.add_argument(
        "--format",
        dest="fmt",
        default=None,
        help=f"Feed format (default: auto-detect). One of: {', '.join(available_formats())}.",
    )
    p.add_argument(
        "--sport",
        default=None,
        help=f"Override sport profile. Known: {', '.join(available_sports())} (else generic).",
    )
    p.add_argument("--assets", default=DEFAULT_ASSETS, help="Assets directory used for page images.")
    p.add_argument("--schema", default=str(DEFAULT_SCHEMA), help="Path to the Story JSON Schema.")
    p.add_argument("--story-id", default=None, help="Explicit story_id (default: generated).")
    p.add_argument("--pretty", action="store_true", help="Pretty-print the output JSON.")
    p.add_argument("--no-validate", action="store_true", help="Skip schema validation.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    squads = [json.loads(Path(s).read_text(encoding="utf-8")) for s in args.squads]

    try:
        story = build_story_from_feed(
            raw,
            squads,
            fmt=args.fmt,
            sport=args.sport,
            assets_dir=args.assets,
            story_id=args.story_id,
            source=Path(args.input).name,
            validate=not args.no_validate,
            schema_path=args.schema,
        )
    except StoryValidationError as exc:
        print("Story failed schema validation:", file=sys.stderr)
        for e in exc.errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if args.pretty else None
    out_path.write_text(json.dumps(story, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")

    n_pages = len(story["pages"])
    print(f"Wrote {out_path} - {n_pages} pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
