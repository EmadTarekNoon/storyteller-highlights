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

## 2. Externalized events configuration
Move the currently hardcoded soccer weights / must-include / caption phrasing
into data so behaviour can be tuned without code changes.
- **Where:** e.g. `config/soccer.yaml|json`; profiles load a config object.
- **What's configurable:** per-event-type weights, must-include set, target
  highlight count, noise types, caption templates, and which stats appear on the
  summary page.
- **Benefit:** non-developers can retune the narrative; A/B different heuristics;
  brand-specific tuning per customer.
- **Effort:** ~half a day (schema + loader + wire into profiles).

## 3. Deployment
Make the builder and viewer easy to run in production.
- **Viewer hosting:** publish `preview/` + a built Story to static hosting
  (GitHub Pages / Netlify / S3+CloudFront). Add a small build step that copies
  `out/story.json` next to the viewer to avoid relative-path juggling.
- **CLI packaging:** publish to PyPI and/or ship a container image; pin deps.
- **CI:** GitHub Actions to run `pytest`, build a sample Story, and validate it
  against the schema on every push; optionally deploy the demo viewer.
- **Effort:** ~half to one day.

## 4. HTTP service mode
Offer the builder as a small API in addition to the CLI.
- **Endpoint:** `POST /stories` accepting a feed (+ optional squads / sport /
  format) and returning the Story JSON; `GET /stories/{id}` to fetch.
- **Where:** a thin `storybuilder.service` module reusing the existing pipeline.
- **Benefit:** integrate directly with a live feed / the Storyteller platform.
- **Effort:** ~half a day (FastAPI/Flask wrapper; logic already factored).

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
- **Where:** slots cleanly into the existing profile seam. Introduce a
  `Narrator` abstraction with two implementations: `TemplateNarrator` (today's
  deterministic logic) and `LLMNarrator` (calls a provider). The profile/pipeline
  depends on the `Narrator` interface, not on how text is produced.
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
