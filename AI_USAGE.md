# AI USAGE

## Tools / models used
- **Devin (Cognition) CLI agent, powered by Claude (Opus).** Used as a pair
  programmer to plan the architecture, scaffold the Python package + web viewer,
  and write tests.

## Where AI helped
- **Exploration & planning:** quickly reading the sample feed, squad files and
  the output JSON Schema, and surfacing the important quirks (events stored
  newest-first, stringly-typed `minute/period/second`, `period 14` end markers,
  opaque team/player ids, and the `pack_id`/`story_id` schema contradiction).
- **Architecture:** shaping the two-seam design (feed `adapters/` + sport
  `profiles/`) so the tool is generic across teams and extensible to other
  sports without touching the core or viewer.
- **Boilerplate & consistency:** generating the dataclasses, adapter/profile
  interfaces, the CLI, and the vanilla-JS Stories viewer, keeping naming and
  docstrings consistent.
- **Tests:** drafting the pytest suite, including the synthetic non-soccer /
  different-teams fixture that proves genericity.

## Prompts or strategies that worked
- Doing a research-first pass over the data + schema before writing any code, and
  writing the findings into a plan, so decisions (e.g. how to handle the schema
  bug) were explicit and reviewable.
- Building end-to-end early (run the CLI, inspect `out/story.json`) and iterating
  on caption quality against real output rather than in the abstract.
- Asking for the design to be split along explicit extension seams up front,
  which kept the generated code modular instead of monolithic.

## Verification steps (tests, assertions, manual checks)
- `pytest` suite (28 tests): adapter normalization/ordering, resolvers,
  soccer scoring/ranking, schema validation (incl. the `pack_id` reconciliation),
  end-to-end Story invariants, and the generic-sport fixture.
- Manual inspection of `out/story.json` (correct running score, goals in order,
  cover reflects real teams/score).
- Manually clicking through the viewer served via `python -m http.server`
  (navigation, autoplay, progress bars, image fallback).

## Cases where I chose NOT to use AI and why
- **Caption generation is deterministic (no LLM at runtime):** captions are built
  from feed fields + the provided commentary so output is reproducible, requires
  no API keys, and can't hallucinate scores/players.
- **Final ranking weights and the schema-bug interpretation** were decided
  deliberately (and documented in `DECISIONS.md`) rather than delegated, since
  they encode product judgement the reviewers are assessing.
