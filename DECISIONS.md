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
  Profiles are **mostly declarative**: the base class turns class attributes
  (`weights`, `scoring`, `must_include_types`, `terms`, …) into behaviour, so a
  new sport is typically a ~10-line subclass (see `basketball.py`). All profiles
  in the package are **auto-discovered/registered** — no registry list to edit.
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
  `info` "Full time" summary page.
- Invariants enforced by tests: first page is `cover`; highlights have
  int `minute` + `headline` + `caption`; highlight minutes are non-decreasing;
  running score is monotonic; all goals appear; the Story validates against the
  schema.

## Full-time summary page
The closing `info` page carries a structured home-vs-away comparison
(Goals, Shots, On target, Corners, Offsides, Fouls, Yellow cards) alongside a
plain-text `body` fallback. The JSON Schema allows additional properties on
`info` pages, so the extra fields (`home_team`, `home_score`, `stats`, …) keep
the Story valid while letting the viewer render a scoreboard + stat bars.
- **Declarative rows:** every sport (including soccer) defines its summary as a
  tuple of `StatRow(label, types, attribute)`; a single base implementation
  counts them, so no profile overrides `info_pages`.
- **Corner attribution fix:** in the source feed a `corner` event's `teamRef1`
  is the *conceding* team (e.g. "Corner, Kilmarnock. Conceded by … (Celtic)" has
  `teamRef1`=Celtic). We verified this from the data and express it declaratively
  with `attribute="opponent"` on the Corners row; shots/offsides/fouls are
  attributed to `teamRef1` as-is (`attribute="acting"`).

## Story viewer (experience)
- Full-bleed vertical "Stories" UI: cover, highlight (photo + minute badge +
  caption), and the full-time summary rendered as a scoreboard with comparison
  bars. Loads `out/story.json` (or `?story=<url>`), resolving asset paths
  relative to the story file.
- Autoplay with segmented progress bars; tap-zones, ←/→, Home/End, and
  Space/press-and-hold controls. Progress fill is set explicitly per segment so
  a *skipped* page's bar fills completely (an inline width was previously left
  mid-animation and overrode the "done" style).
- Long captions are clamped in CSS (full text stays in the JSON) so a slide
  never overflows.
- **Accessibility:** labelled story region, `aria-live` page announcements
  ("Page X of Y — headline"), `aria-current` on the active segment, dynamic
  play/pause labels, visible `:focus-visible` outlines, and a
  `prefers-reduced-motion` path that disables animation.

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

## What's next
The prioritized backlog now lives in `docs/ROADMAP.md` (new sport profiles,
externalized events configuration, deployment, viewer upgrades such as team
colours/swipe/match-picker, optional AI caption polish, and an HTTP service).
Short version of the highest-value items:
- A second real profile (e.g. rugby/basketball) beyond the generic fallback.
- Smarter narrative pacing (dedupe near-duplicate penalty won/lost into one
  build-up; balance team/half representation).
- Team crests/colours in the viewer driven by feed metadata.
