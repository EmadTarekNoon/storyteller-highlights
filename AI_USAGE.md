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
  generic across teams and sports without touching the core or viewer.
- **Extensibility work:** making profiles mostly **declarative** with a base that
  derives scoring/ranking/captions/summary from class attributes, **auto-discovery**
  of profiles (no registry edits), and a unified `StatRow`-driven full-time
  summary used by every sport (soccer refactored onto it with byte-identical
  output). Added a `BasketballProfile` as a worked example.
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
- `pytest` suite (**32 tests**): adapter normalization/ordering, resolvers,
  soccer scoring/ranking, schema validation (incl. the `pack_id` reconciliation),
  end-to-end Story invariants, a generic non-soccer/different-teams fixture, and
  a new-sport (basketball) fixture that proves the declarative path.
- Byte-identical check when refactoring the summary onto `StatRow`.
- `node --check` on `preview/viewer.js`; manual click-throughs of three matches
  (soccer, and the Arsenal/Madrid + basketball examples) via `python -m http.server`.

## Cases where I chose NOT to use AI and why
- **Caption generation is deterministic (no LLM at runtime):** captions are built
  from feed fields + the provided commentary so output is reproducible, needs no
  API keys, and can't hallucinate scores/players. (An **optional** `LLMNarrator`
  is proposed in `docs/ROADMAP.md`, gated by the `EVALS.md` checks with a
  deterministic fallback — deliberately not enabled by default.)
- **Ranking weights, the schema-bug interpretation, and the corner-attribution
  fix** were decided deliberately (and documented in `DECISIONS.md`) rather than
  delegated, since they encode product judgement the reviewers are assessing.
