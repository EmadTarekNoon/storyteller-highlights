# Features

This document describes what the tool does today and how to extend it. For the
forward-looking backlog see [ROADMAP.md](./ROADMAP.md).

## What it is
`storybuilder` ingests a sports match feed and produces a schema-valid **Story**
— a JSON bundle of **Pages** — plus a zero-dependency **web viewer** that plays
the Story back as a tap-through "Stories" experience. It is built so that
neither the teams nor the sport are hardcoded.

## High-level flow
```
feed (+squads)  ->  adapter  ->  Match model  ->  profile (rank + caption)
                                                        |
                          assets + running score  ->  Story pages
                                                        |
                                   jsonschema validate  ->  out/story.json
                                                        |
                                              preview/ viewer renders it
```

## Current features

### Builder (Python CLI)
- **Feed ingestion** with normalization: reverses newest-first feeds, sorts by
  `(period, minute, second)`, coerces string numbers to ints, drops synthetic
  `period 14/16` end markers, and de-duplicates events.
- **Reference resolution:** team ids resolve from `matchInfo.contestant`; player
  ids from any number of `--squads` files. Unresolved ids fall back to the name
  in the human `comment`, so raw ids never surface.
- **Ranking heuristic:** per-event importance weights from the active sport
  profile, with "must-include" events (goals, red/second-yellow cards,
  penalties) always kept; remaining slots filled by weight, then re-sorted
  chronologically. Each highlight carries an `explanation`.
- **Deterministic captions:** built from event fields + source commentary (no
  AI at runtime). Goal captions guarantee minute + player + running score.
- **Running score:** tracked across the timeline by the profile so captions and
  the scoreboard reflect the correct scoreline at each moment.
- **Full-time summary page:** structured home-vs-away stats (Goals, Shots, On
  target, Corners, Offsides, Fouls, Yellow cards) plus a text fallback.
- **Assets:** deterministic, reproducible image selection with a placeholder
  fallback (provided images are decorative, not event-accurate).
- **Validation:** every Story is validated against `schema/story.schema.json`
  with `jsonschema` (date-time format checking) before it is written.
- **CLI flags:** `--in`, `--out`, `--squads`, `--format`, `--sport`, `--assets`,
  `--schema`, `--story-id`, `--pretty`, `--no-validate`.

### Pluggable architecture (two seams)
- **Feed adapters** (`src/storybuilder/adapters/`): map a raw provider feed into
  the internal `Match` model. `opta_soccer` handles the sample feed's format.
  Selection is explicit (`--format`) or auto-detected.
- **Sport profiles** (`src/storybuilder/profiles/`): supply sport semantics —
  scoring, ranking weights, must-include rules, caption terminology, cover, info
  pages, and metrics. A registry selects a profile from the feed's `sport.name`
  with a `GenericProfile` fallback (`--sport` overrides). `SoccerProfile` is the
  concrete implementation.
- The **core** (`pipeline.py`, `story.py`, `validate.py`) and the **viewer** are
  entirely sport-agnostic.

### Story viewer (`preview/`)
- Full-bleed vertical Stories UI: cover, highlight (photo + minute badge +
  caption), and the full-time scoreboard/stat-comparison page.
- Autoplay with segmented progress bars; navigation via tap-zones, ← / →,
  Home/End, and Space/press-and-hold to pause.
- Loads `out/story.json` by default or any `?story=<url>`, resolving asset paths
  relative to the story file.
- **Accessibility:** labelled story region, `aria-live` page announcements,
  `aria-current` progress state, dynamic play/pause labels, `:focus-visible`
  outlines, and `prefers-reduced-motion` support.
- Long captions are visually clamped so slides never overflow (full text stays
  in the JSON).

### Output contract
Top-level: `story_id`, `title`, `source`, `created_at`, `metrics`, `pages`.
Page types: `cover`, `highlight`, `info`. See `schema/story.schema.json` and the
`pack_id`/`story_id` note in `DECISIONS.md`.

### Tests
`pytest` suite covering adapter normalization/ordering, id resolution, soccer
scoring/ranking, schema validation (incl. the schema reconciliation), end-to-end
Story invariants, and a synthetic different-teams / non-soccer genericity
fixture.

### Examples
`examples/` contains two synthetic soccer feeds (Arsenal 2–2 Liverpool, Real
Madrid 3–1 Barcelona) shaped like the real feed, to demonstrate the viewer
across different teams and scorelines.

## How to extend today

### Add a new sport
1. Create `src/storybuilder/profiles/<sport>.py` subclassing `SportProfile`.
2. Implement `score_delta`, `weight`, `caption`, `cover` (and optionally
   `must_include`, `info_pages`, `metrics`); set `handles = ("<sport>", …)`.
3. Register it in `profiles/__init__.py` (`_PROFILES`).
The registry then auto-selects it when a feed's `sport.name` matches, or via
`--sport <sport>`. No core or viewer changes required.

### Add a new feed provider
1. Create `src/storybuilder/adapters/<provider>.py` subclassing `FeedAdapter`.
2. Implement `can_parse(raw)` (for auto-detection) and
   `parse(raw, squads, source)` returning a `Match`.
3. Register it in `adapters/__init__.py` (`_ADAPTERS`).
Select via `--format <name>` or rely on auto-detection.

### Point the viewer at a different Story
Serve the repo root and open `preview/?story=<relative-or-absolute-url>`.
