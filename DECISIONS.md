# DECISIONS

## Overview
The builder is a small Python package (`src/storybuilder`) plus a zero-dependency
web viewer (`preview/`). It ingests a match feed, ranks the events into a
narrative, and emits a schema-valid Story (`out/story.json`). The design keeps a
**sport-agnostic core** and pushes everything provider- or sport-specific behind
two small seams so it works for **any two teams** and can **scale to other
sports**.

## Architecture (two extension seams)
- **`FeedAdapter` (`adapters/`)** — parses a raw provider feed into the internal
  `Match` model. `opta_soccer.py` absorbs this feed's quirks; a new provider is
  just a new adapter. Selected via `--format` or auto-detection.
- **`SportProfile` (`profiles/`)** — supplies sport semantics: scoring/running
  score, ranking weights, must-include events, caption templates/terminology,
  and info/stats pages. A registry picks a profile from the feed's
  `sport.name`, falling back to a **`GenericProfile`** so an unknown sport still
  yields a valid Story. `SoccerProfile` is the concrete implementation.
- The **core** (`pipeline.py`, `story.py`, `validate.py`) and the **web viewer**
  are entirely sport-agnostic — the viewer only knows about `cover`/`highlight`/
  `info` pages, so new sports/teams need zero viewer changes.

## Heuristic and ranking
- Each event gets an importance **weight** from the profile (soccer: goal/penalty
  goal 100 → free kick lost 8), with a sensible default for unseen types.
- **Must-include** events (goals, red/second-yellow cards, penalties) are always
  kept regardless of the slot budget; remaining slots (target ~10) are filled by
  descending weight, then the final set is re-sorted **chronologically**.
- Structural/administrative events (`lineup`, `start`, `end*`, delays) are
  treated as noise and never become standalone highlights.
- Each highlight carries a short `explanation` of why it was chosen.

## Data handling (duplicates, missing fields, out-of-order minutes)
- **Reverse order:** the feed is stored newest-first; events are reversed then
  sorted ascending by `(period, minute, second)` (stable sort preserves intra-
  timestamp order).
- **Stringly-typed numbers:** `minute`/`period`/`second` arrive as strings and
  are coerced to ints (bad values default to 0 rather than crashing).
- **Synthetic markers:** `period` 14/16 ("match end") are dropped so they don't
  pollute the timeline or stats.
- **Duplicates:** de-duplicated by event id (fallback: type+time+comment).
- **Missing fields:** missing `playerRef1` is tolerated; unresolved ids fall back
  to the name embedded in the human `comment`, so a raw id never surfaces.
- **Opaque ids:** teams resolve from `matchInfo.contestant`; players from any
  number of `--squads` files (Opta `squad[].person[].matchName`). Nothing is
  hardcoded to Celtic/Kilmarnock.

## Captions
- Deterministic templates (no AI). Goal captions reuse the rich source
  commentary (scorer, shot type, assist) and append the running scoreline;
  headlines carry the minute + score. This guarantees **minute + player + score**
  presence for goals (see `EVALS.md`).

## Pack structure and invariants
- Output fields: `story_id`, `title`, `source`, `created_at` (ISO-8601 UTC),
  `metrics` (final score, goal count, per-type counts), and `pages`.
- Pages: exactly one `cover` first, chronological `highlight` pages, then an
  `info` "Match stats" page.
- Invariants enforced by tests: first page is `cover`; highlights have
  int `minute` + `headline` + `caption`; highlight minutes are non-decreasing;
  running score is monotonic; all goals appear; the Story validates against the
  schema.

## Schema quirk (`pack_id` vs `story_id`)
`schema/story.schema.json` lists `pack_id` in `required` but only defines
`story_id` in `properties`, **and** sets `additionalProperties: false` at the top
level. As written this is **unsatisfiable** — a document cannot both provide
`pack_id` (required) and omit it (forbidden). Interpreting the intent as
`story_id` (which matches the defined properties, both READMEs and the
invariants), we emit `story_id` and, at validation time only, reconcile the
**schema** by mapping `pack_id → story_id` in `required`. This is isolated in
`validate.py` and covered by a test.

## Assets
The provided images are generic (not tied to specific events), so they are used
decoratively: a fixed cover image and a stable per-event pick (hash of the
event) so the same event always gets the same picture, with a placeholder
fallback. Documented as decorative, not event-accurate.

## What I would do with 2 more hours
- Add a second real profile (e.g. rugby/basketball) to exercise the profile seam
  beyond the generic fallback.
- Smarter narrative pacing (momentum/xG-style weighting, dedupe near-duplicate
  penalty won/lost pairs into a single build-up).
- Team crests/colours in the viewer driven by feed metadata; per-half section
  dividers; share/export of a single page as an image.
- Optional AI caption polish behind a flag, with the eval harness gating output.
