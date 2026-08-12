# Highlights → Stories Mini‑Builder (Tech‑agnostic Scaffold)

**Goal:** Ingest sports match events and produce a **Story** (a JSON bundle of Pages) plus a **preview** to step through Pages.

You can implement the builder in any language as a **CLI** or **small HTTP service**. This scaffold includes:
- A **data contract** for events.
- A **JSON Schema** for the output story.
- Templates for `DECISIONS.md`, `AI_USAGE.md`, and test invariants.

Your goal is to produce the best possible Story based summary of the game and the best possible experience for viewing that Story.

How you achieve that is up to you. The below information serves to explain what you can see in this repository that you might wish to draw on as part of the above.

## Repository layout
- `data/` — The raw data which you have to work with `match_events.json` here (see `data/events_schema.md`).
- `assets/` — Images which you may wish to use in your Story JSON and Story Viewer.
- `out/` — The output JSON files which you produce. Add `.gitkeep` to keep the folder.
- `schema/pack.schema.json` — JSON Schema for validating the output pack.
- `preview/` — A place to put the Story viewer which you build.
- `tests/` - An empty tests folder which you might want to populate.
- `templates/DECISIONS.md`, `templates/AI_USAGE.md`, `templates/EVALS.md` — Template documents you can fill in.

Good luck, and have fun! Keep it simple and explain your thought process clearly.

---

## Solution (this submission)

A small **Python** builder (`src/storybuilder`) turns a match feed into a
schema-valid Story (`out/story.json`), and a **zero-dependency web viewer**
(`preview/`) plays it back as a tap-through "Stories" experience.

### Design: generic by construction
Nothing is hardcoded to Celtic/Kilmarnock or to soccer. The core is
sport-agnostic and everything specific lives behind two small seams:
- **`adapters/`** — parse a provider feed into the internal `Match` model
  (`opta_soccer.py` handles this feed's quirks). New provider = new adapter.
- **`profiles/`** — sport semantics (scoring, ranking weights, captions). A
  registry selects one from the feed's `sport.name`, with a `GenericProfile`
  fallback so unknown sports still produce a valid Story. New sport = new profile.

Each Story is: a **cover**, a set of chronological **highlight** pages, and a
**full-time summary** page (scoreboard + home-vs-away stat comparison). The
viewer is a full-bleed vertical Stories UI with autoplay, segmented progress
bars, keyboard/tap navigation, and accessibility support.

### Documentation
- `docs/FEATURES.md` — full list of current features + how to extend (add a
  sport, add a feed adapter).
- `docs/ROADMAP.md` — planned next features (new sports, events configuration,
  deployment, viewer upgrades, AI captions, HTTP service, …).
- `DECISIONS.md` — design rationale + data handling. `AI_USAGE.md`, `EVALS.md`.

### Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    |    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

### Build the Story
```bash
python -m storybuilder \
  --in data/match_events.json \
  --squads data/celtic-squad.json data/kilmarnock-squad.json \
  --out out/story.json --pretty
```
Useful flags: `--format` (feed adapter, default auto-detect), `--sport`
(override profile), `--no-validate`.

### Preview the Story
Serve from the repo root, then open the viewer:
```bash
python -m http.server 8000
# open http://localhost:8000/preview/
```
Controls: side tap-zones or ← / → to navigate, **Home/End** to jump to
first/last, **Space** (or press-and-hold) to pause. Screen-reader live region
announces each page; respects `prefers-reduced-motion`.

### Try other matches
Two extra synthetic soccer feeds live in `examples/`. Build and view them with
the same viewer via the `?story=` query param:
```bash
python -m storybuilder --in examples/arsenal-liverpool.json --out out/story-arsenal-liverpool.json --pretty
python -m storybuilder --in examples/madrid-barcelona.json  --out out/story-madrid-barcelona.json  --pretty
# then open, e.g.:
# http://localhost:8000/preview/?story=../out/story-arsenal-liverpool.json
```

### Test
```bash
pytest
```
