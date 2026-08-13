# EVALS

Captions are **deterministic** (built from feed fields + the provided
commentary), so there is no LLM output to grade for hallucination. Instead the
eval focuses on **completeness and readability**: does every goal caption carry
the three things a reader needs — the **minute**, the **player**, and the
**running score** — and does it read cleanly?

## Quality check
For each goal/penalty-goal highlight we assert (in `tests/test_profiles.py`
`test_goal_caption_has_minute_player_and_score`):
- minute present (headline contains `NN'`)
- scoreline present (headline contains `H-A`, caption ends with the full
  `Home H-A Away`)
- player present (scorer name appears in the caption)

We also assert the running score is **monotonic** across highlights and that
**all** goals are included, so no scoring moment is dropped or mis-ordered.

The same guarantees hold for other feeds and sports: the caption structure is
shared, so the Arsenal/Madrid example matches and the basketball example
(`terms`-driven labels like `DUNK`/`THREE`, running score in the headline) read
consistently.

## Full-time summary correctness
The summary page's per-team counts are derived declaratively via
`StatRow(label, types, attribute)`. The one non-obvious case is **corners**:
the feed's `teamRef1` on a `corner` event is the *conceding* team, verified
against the data (e.g. "Corner, Kilmarnock. Conceded by … (Celtic)" carries
`teamRef1`=Celtic). We encode this as `attribute="opponent"` on the Corners row;
all other rows use `attribute="acting"`. Sanity-checked against the sample match
(Celtic dominance: 21 shots to 3, 7 on target to 1). A dedicated unit test for
these counts is listed in `docs/ROADMAP.md`.

## When the LLM narrator lands
Captions are deterministic today. The proposed optional `LLMNarrator`
(`docs/ROADMAP.md`) is designed to be gated by exactly these checks — minute /
player / score presence, length, and no hallucinated scoreline — and to fall
back to the deterministic caption whenever a generated string fails, so quality
never regresses below the template baseline.

## Before / after examples
"Before" = the raw feed `comment`. "After" = the page the builder emits
(`headline` + `caption`).

### 1. Opening goal (9')
- **Before:** `Goal! Celtic 1, Kilmarnock 0. Johnny Kenny (Celtic) left footed shot from very close range to the bottom left corner. Assisted by Reo Hatate.`
- **After — headline:** `9' GOAL - Celtic 1-0 Kilmarnock`
- **After — caption:** `Johnny Kenny (Celtic) left footed shot from very close range to the bottom left corner. Assisted by Reo Hatate. Celtic 1-0 Kilmarnock.`
- *Why better:* the minute + scoreline are promoted into a scannable headline; the
  descriptive detail (shot type, assist) is preserved; the running score is
  restated cleanly instead of the terse `Celtic 1, Kilmarnock 0` prefix.

### 2. Second-half strike (50')
- **Before:** `Goal! Celtic 2, Kilmarnock 0. Kieran Tierney (Celtic) left footed shot from outside the box to the bottom right corner. Assisted by Liam Scales.`
- **After — headline:** `50' GOAL - Celtic 2-0 Kilmarnock`
- **After — caption:** `Kieran Tierney (Celtic) left footed shot from outside the box to the bottom right corner. Assisted by Liam Scales. Celtic 2-0 Kilmarnock.`
- *Why better:* consistent structure with the other goals; minute/score/scorer all
  present and immediately visible.

### 3. Stoppage-time penalty (92')
- **Before:** `Goal! Celtic 4, Kilmarnock 0. Arne Engels (Celtic) converts the penalty with a right footed shot to the bottom left corner.`
- **After — headline:** `92' PENALTY GOAL - Celtic 4-0 Kilmarnock`
- **After — caption:** `Arne Engels (Celtic) converts the penalty with a right footed shot to the bottom left corner. Celtic 4-0 Kilmarnock.`
- *Why better:* the penalty is labelled distinctly in the headline; the caption
  keeps the conversion detail and appends the final scoreline.
