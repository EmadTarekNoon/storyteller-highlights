# AI USAGE

## Tools / models used
- **Devin (Cognition) CLI agent, powered by Claude (Opus).** Used as a pair
  programmer to plan the architecture, scaffold the Python package + web viewer,
  write tests, iterate on the viewer UX, and handle the GitHub setup.

## Where AI helped
- **Exploration & planning:** reading the sample feed, squad files and the output
  JSON Schema, and surfacing the important quirks (events stored newest-first,
  stringly-typed `minute/period/second`, `period 14` end markers, opaque
  team/player ids, and the `pack_id`/`story_id` schema contradiction).
- **Architecture:** shaping the swappable-seam design — feed `adapters/` + sport
  `profiles/` over a stable `Match`/`Event`/`Story` model — so the tool is
  generic across teams and sports without touching the core or viewer. A later
  maturity pass decomposed the profile into five collaborators in `behaviors/`
  (`Scorer`, `Ranker`, `Narrator`, `PageComposer`, `HighlightSelector`), made
  pages typed + self-describing (`pages.py`), externalized per-sport config
  (`config/`), and extracted a reusable orchestration entry point (`app.py`)
  shared by the CLI and an optional FastAPI service (`service.py`).
- **Extensibility work:** profiles are **declarative** (a base wires class
  attributes to default collaborators, each independently swappable — e.g. a
  `SoccerNarrator`/`SoccerComposer` or a future `LLMNarrator`), with
  **auto-discovery** of both profiles and adapters (no registry edits) and a
  unified `StatRow`-driven full-time summary. Pages are typed dataclasses that
  own their JSON-Schema fragment (a test enforces builder↔schema parity), and
  the viewer renders them through a **renderer registry**. Added a
  `BasketballProfile` as a worked example.
- **Builder logic:** ingest/normalize, id→name resolution, ranking heuristic,
  deterministic captions, running score, assets, and jsonschema validation.
- **Viewer + UX:** the vanilla-JS Stories viewer, the redesigned full-time
  scoreboard/stat-comparison page, and fixes driven by preview feedback
  (progress bar filling on skip, caption clamping, and an accessibility pass:
  aria-live announcements, focus outlines, reduced-motion, Home/End keys).
- **Tests & docs:** the pytest suite (incl. genericity and new-sport fixtures),
  `docs/FEATURES.md`, `docs/ROADMAP.md`, and keeping `README`/`DECISIONS` current.
- **Environment & delivery:** installed Python + the GitHub CLI on a fresh
  machine, set up the venv, and created/committed/pushed the public repo.

## Prompts or strategies that worked
- Research-first passes over the data + schema, written into a plan before any
  code, so decisions (e.g. handling the schema bug) were explicit and reviewable.
- Planning-mode design reviews before implementing larger changes.
- Building end-to-end early (run the CLI, inspect `out/story.json`, open the
  viewer) and iterating against real output and preview screenshots.
- On refactors, asserting **behaviour is unchanged** (regenerating the soccer
  Story and diffing it to prove byte-identical output).
- Designing along explicit extension seams so new requirements are additive.

## Verification steps (tests, assertions, manual checks)
- `pytest` suite (**57 tests**): adapter normalization/ordering, resolvers,
  soccer scoring/ranking, schema validation (incl. the `pack_id` reconciliation),
  end-to-end Story invariants, a generic non-soccer/different-teams fixture, a
  new-sport (basketball) fixture, plus the maturity-pass additions — typed-page
  round-trips + schema/registry parity (`test_pages.py`), the orchestration
  entry point (`test_app.py`), config load/override + default parity
  (`test_config.py`), and the FastAPI service via `TestClient` (`test_service.py`).
- `ruff` + `black` clean across `src` and `tests`.
- Behaviour-preservation checks on the refactor (config parity test proves the
  externalized `config/soccer.json` reproduces the built-in profile exactly).
- Manual click-throughs of all four Stories (soccer + Arsenal/Madrid + basketball)
  via `python -m http.server`.

## Cases where I chose NOT to use AI and why
- **Caption generation is deterministic (no LLM at runtime):** captions are built
  from feed fields + the provided commentary so output is reproducible, needs no
  API keys, and can't hallucinate scores/players. The `Narrator` **seam** now
  exists (`behaviors/narration.py`) so an **optional** `LLMNarrator` can be added
  later — gated by the `EVALS.md` checks with a deterministic fallback — but it is
  deliberately not enabled by default.
- **Ranking weights, the schema-bug interpretation, and the corner-attribution
  fix** were decided deliberately (and documented in `DECISIONS.md`) rather than
  delegated, since they encode product judgement the reviewers are assessing.
