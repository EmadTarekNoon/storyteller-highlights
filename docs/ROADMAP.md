# Roadmap

Forward-looking features, roughly in priority order. Each item notes the intent,
where it would live, and rough effort. Current capabilities are in
[FEATURES.md](./FEATURES.md).

## 1. More sport types
Add real profiles beyond the `GenericProfile` fallback.
- **Where:** `src/storybuilder/profiles/<sport>.py` + register in
  `profiles/__init__.py`.
- **Examples:** rugby (tries/conversions/penalties, sin-bin), basketball
  (2/3-pointers, quarters, lead changes), cricket (wickets/boundaries, overs).
- **Notes:** each profile defines its own scoring model, ranking weights,
  caption terminology, and stat rows. Period handling generalizes since the
  model already uses `(period, minute, second)`.
- **Effort:** ~half a day per sport.

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

## 7. Optional AI caption enrichment
Keep deterministic captions as the default; add an opt-in flag to polish phrasing
via an LLM.
- **Where:** a `captions` enricher invoked only when `--ai` is set + an API key
  is present.
- **Guardrails:** run the existing eval checks (minute/player/score presence)
  and fall back to the deterministic caption if the model output fails them.
- **Effort:** ~half a day plus eval tuning.

## 8. Richer media pipeline
- Map events to event-accurate imagery/video where available (goal clips, player
  photos) instead of decorative stock images.
- Support remote asset URLs/CDN in the Story JSON.
- **Effort:** depends on media source; ~1 day for URL support.

## 9. Internationalization
- Select the commentary language from the feed's `messages[].language` and
  localize generated caption/label strings.
- **Effort:** ~half a day for language selection; more for full string catalogs.

## 10. Additional tests / tooling
- Unit tests for the per-team summary stats (incl. the corner-attribution flip)
  and the asset picker's stability.
- CLI-level smoke test and a lint/format config (ruff/black).
- **Effort:** ~2–3 hours.
