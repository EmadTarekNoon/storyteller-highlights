# Roadmap

Forward-looking features, roughly in priority order. Each item notes the intent,
where it would live, and rough effort. Current capabilities are in
[FEATURES.md](./FEATURES.md).

## 1. More sport types
Add real profiles beyond the `GenericProfile` fallback. The declarative base +
auto-discovery already make this cheap (a soccer and a basketball profile ship
today; see `docs/FEATURES.md` "Add a new sport").
- **Where:** just drop `src/storybuilder/profiles/<sport>.py`; it auto-registers.
- **Examples:** rugby (tries/conversions/penalties, sin-bin), cricket
  (wickets/boundaries, overs), American football (TD/FG/extra point).
- **Notes:** simple sports need only class attributes (`scoring`, `weights`,
  `must_include_types`, `terms`); override `caption`/`info_pages` only for richer
  narration. Period handling generalizes since the model uses
  `(period, minute, second)`.
- **Effort:** ~10 lines / minutes for a basic sport; more for rich captions.

## 2. Externalized events configuration — DONE (initial)
Hardcoded soccer weights / must-include / scoring / summary rows can now be
tuned via data instead of code.
- **Where:** `config/<sport>.json` (loaded by `config.py`, applied on top of the
  profile's declarative defaults; `config/soccer.json` ships at parity).
- **What's configurable today:** per-event-type weights, must-include set,
  target highlight count, noise types, scoring, terms, `score_label`, and the
  summary rows.
- **Still to do:** caption *template* strings (currently code), a JSON Schema
  for the config file, and optional YAML support.

## 3. Deployment
Make the builder and viewer easy to run in production.
- **Viewer hosting:** publish `preview/` + a built Story to static hosting
  (GitHub Pages / Netlify / S3+CloudFront). Add a small build step that copies
  `out/story.json` next to the viewer to avoid relative-path juggling.
- **CLI packaging:** publish to PyPI and/or ship a container image; pin deps.
- **CI:** GitHub Actions to run `pytest`, build a sample Story, and validate it
  against the schema on every push; optionally deploy the demo viewer.
- **Effort:** ~half to one day.

## 4. HTTP service mode — DONE (initial)
The builder is exposed as an API in addition to the CLI.
- **Where:** `storybuilder.service` (FastAPI, `[service]` extra) reusing the
  shared `app.build_story_from_feed` orchestration; run with `storybuilder-serve`.
- **Endpoints today:** `POST /stories` (feed + optional squads / sport / format)
  → Story JSON; `GET /healthz`.
- **Still to do:** persistence + `GET /stories/{id}`, auth, and rate limiting.

## 5. Viewer experience upgrades
- **Team branding:** club colours/crests driven by feed metadata (map contestant
  codes to a palette) instead of the generic green/red bars and stock photos.
- **Persistent scoreboard chrome** on highlight pages (mini scoreline + clock).
- **Touch swipe** navigation and subtle Ken Burns image motion / page
  transitions (all gated behind `prefers-reduced-motion`).
- **Match picker UI** to switch between available Stories instead of the
  `?story=` query param.
- **Share/export** a single page as an image.
- **Effort:** incremental; ~1–2 days for the full set.

## 6. Narrative quality
- Dedupe near-duplicate beats (e.g. penalty won + penalty lost at the same
  minute) into a single build-up.
- Balance selection so both teams and both halves are represented.
- Add structural beats: half-time marker, an opening "how it unfolded" intro,
  and a closing player-of-the-match / turning-point page.
- **Effort:** ~half a day.

## 7. LLM-generated page content (better UX)
Pass structured event data to an LLM to generate richer, more natural page
content — headlines, captions, cover/subheadlines, and short narrative "info"
beats (e.g. "how the half unfolded") — while keeping the deterministic templates
as the guaranteed fallback.
- **Where:** the `Narrator` seam already exists (`behaviors/narration.py`, with
  `TemplateNarrator` as today's deterministic default; soccer uses a
  `SoccerNarrator`). Remaining work is just an `LLMNarrator` implementation that
  calls a provider — the profile/pipeline already depend only on the interface.
- **Input contract:** send the LLM a compact, typed payload per selected event
  (minute, type, team/player names, running score, source commentary) plus match
  context — never raw ids — so it has everything to write good copy.
- **Config:** opt-in via `--narrator llm` (or per-profile), API key from env;
  model + prompt templates configurable (ties into item 2's config work).
- **Guardrails / evals:** validate every generated string against the existing
  checks (minute/player/score presence, length, no hallucinated score) and fall
  back to the template caption if it fails; cache by event id for determinism in
  tests; keep a `--no-ai` reproducible mode.
- **Effort:** ~1 day for the seam + a provider + eval gating.

## 8. Per-sport media / picture handling
Replace the decorative, hash-picked stock images with a proper, sport-aware
media layer so each page shows appropriate visuals.
- **Where:** promote `assets.py` into an `ImageProvider` interface selected per
  sport (parallel to profiles/adapters). Implementations: `LocalAssets` (today),
  `SportPackAssets` (a per-sport image pack keyed by event *category* — goal,
  card, save, dunk, three, …), and `RemoteAssets` (CDN/URLs, incl. event-accurate
  photos/clips and player/club imagery where a media feed provides them).
- **Category mapping:** profiles already know event semantics; add a small
  `image_category(event)` (declarative map, like `terms`) so the provider can
  choose art that matches the moment for *any* sport.
- **Fallback chain:** event-accurate media -> sport-pack category image ->
  placeholder, so it degrades gracefully.
- **Viewer:** already supports remote/relative image URLs; add team crest/colour
  theming from feed metadata.
- **Effort:** ~1 day for the provider seam + a sport pack; more for real media.

## 9. Internationalization
- Select the commentary language from the feed's `messages[].language` and
  localize generated caption/label strings.
- **Effort:** ~half a day for language selection; more for full string catalogs.

## 10. Additional tests / tooling
- Unit tests for the per-team summary stats (incl. the corner-attribution flip)
  and the asset picker's stability.
- CLI-level smoke test and a lint/format config (ruff/black).
- **Effort:** ~2–3 hours.
