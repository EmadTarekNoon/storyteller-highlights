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

### Pluggable architecture (swappable seams)
- **Feed adapters** (`src/storybuilder/adapters/`): map a raw provider feed into
  the internal `Match` model. `opta_soccer` handles the sample feed's format.
  Adapters are **auto-discovered** (drop a module, set `name`); selection is
  explicit (`--format`) or auto-detected (by `priority`, then `can_parse`).
- **Sport profiles** (`src/storybuilder/profiles/`): supply sport semantics.
  A registry selects a profile from the feed's `sport.name` with a
  `GenericProfile` fallback (`--sport` overrides). A profile is a **declarative
  bag of config** wired to five collaborators it can swap independently:
  **`behaviors/`** — `Scorer`, `Ranker`, `Narrator`, `PageComposer`,
  `HighlightSelector`. `SoccerProfile` swaps in a `SoccerNarrator` +
  `SoccerComposer`; `GenericProfile` swaps in a `NullScorer` + `KeywordRanker`.
- **Typed pages** (`src/storybuilder/pages.py`): `cover` / `highlight` / `info` /
  `summary` are dataclasses that own both their serialization and their JSON
  Schema fragment (single source of truth; a test enforces schema parity).
- **Externalized config** (`config/<sport>.json`): per-sport weights,
  must-include, scoring, terms, and summary rows as data (see below).
- **Orchestration** (`src/storybuilder/app.py`): `build_story_from_feed(...)` is
  the one entry point shared by the CLI and the optional FastAPI service
  (`src/storybuilder/service.py`).
- The **core** (`pipeline.py`, `story.py`, `validate.py`) and the **viewer** are
  entirely sport-agnostic; the viewer renders pages via a **renderer registry**
  keyed by page `type`.

### Design principles (built to absorb new requirements)
The system is organized around small, swappable seams behind a stable internal
model (`Match`/`Event`/`Story`), so new requirements slot in without redesign:
- **Data in** varies by provider -> `FeedAdapter`.
- **Meaning** varies by sport -> `SportProfile` (mostly declarative, auto-registered).
- **Presentation** is data-only pages (`cover`/`highlight`/`info`) rendered by a
  dumb, sport-agnostic viewer.
- Everything specific is declarative where possible (weights, scoring, terms,
  `summary_stats`) and validated against the schema on the way out.
This is why upgrades stay additive rather than rewrites: the `Narrator` seam is
already in place (an `LLMNarrator` just implements the interface), and per-sport
media would follow the same pattern as a future `ImageProvider` seam — the core
and viewer stay unchanged.

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
Page types: `cover`, `highlight`, `info` (generic text), and `summary` (the
full-time scoreboard + stat comparison). Each is a typed dataclass in `pages.py`
that owns its schema fragment. See `schema/story.schema.json` and the
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

### Add a new sport (usually ~10 lines, no wiring)
Drop one file in `src/storybuilder/profiles/` with a `SportProfile` subclass that
sets a few **declarative class attributes**. It is **auto-discovered and
registered** — there is no registry list to edit, and the base class provides
scoring, ranking, captions, cover, the full-time page and metrics from your
attributes. Example (`profiles/basketball.py`):

```python
from .base import SportProfile

class BasketballProfile(SportProfile):
    handles = ("basketball",)
    scoring = {"3 points": 3, "2 points": 2, "free throw": 1, "dunk": 2, "buzzer beater": 2}
    weights = {"buzzer beater": 100, "dunk": 80, "3 points": 60, "2 points": 40, "free throw": 20}
    must_include_types = frozenset({"buzzer beater", "dunk"})
    terms = {"3 points": "THREE", "dunk": "DUNK", "buzzer beater": "BUZZER BEATER"}
```

Configurable attributes: `handles`, `target_highlights`, `weights`,
`default_weight`, `must_include_types`, `scoring`, `own_types` (scoring events
that credit the opponent, e.g. own goals), `terms`, `noise_types`, and — for the
full-time summary — `score_label` and `summary_stats`.

`summary_stats` is a tuple of `StatRow(label, types, attribute)` rows rendered as
home-vs-away comparison bars. `attribute` is `"acting"` (credit the event's own
team, the default) or `"opponent"` (credit the other side, e.g. soccer corners
where the feed references the conceding team). The default `SummaryComposer`
renders these rows for every sport — even soccer defines its rows this way
(`Shots`, `On target`, `Corners` with `attribute="opponent"`, `Offsides`,
`Fouls`, `Yellow cards`).

The registry auto-selects the profile when a feed's `sport.name` matches (or via
`--sport <sport>`); unknown sports fall back to `GenericProfile`. For richer
behaviour, swap a **collaborator** rather than the whole profile: return a custom
`Narrator` / `PageComposer` from the matching property — `soccer.py` does this
(`SoccerNarrator` for commentary-driven captions, `SoccerComposer` for a
detailed stats page + metrics). No core or viewer changes are ever required.

### Add a new feed provider
1. Create `src/storybuilder/adapters/<provider>.py` subclassing `FeedAdapter`.
2. Set a unique `name` (and optionally a `priority`; lower is tried first).
3. Implement `can_parse(raw)` (for auto-detection) and
   `parse(raw, squads, source)` returning a `Match`.
It is **auto-discovered** — no registry list to edit. Select via
`--format <name>` or rely on auto-detection.

### Tune a sport without code
Create `config/<sport>.json` with any of `target_highlights`, `default_weight`,
`weights`, `scoring`, `must_include_types`, `own_types`, `terms`, `noise_types`,
`score_label`, and `summary_stats` (list of `{label, types, attribute}`). It is
applied on top of the profile's defaults when a feed selects that sport (or via
`get_profile(sport, config_dir=...)` / `build_story_from_feed(config_dir=...)`
for a custom config set). See `config/soccer.json`.

### Swap how captions are produced (e.g. an LLM narrator)
Implement the `Narrator` protocol (`behaviors/narration.py`) and return it from
your profile's `narrator` property. The pipeline depends only on the interface,
so a future `LLMNarrator` slots in with no core/viewer changes.

### Point the viewer at a different Story
Serve the repo root and open `preview/?story=<relative-or-absolute-url>`.
