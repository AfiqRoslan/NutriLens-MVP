# NutriLens (MVP)

## What this is

A university startup MVP testing whether budget-conscious students will use
a tool that recommends a meal based on **budget** and a **nutrition goal**
*before* they order. Single-page Streamlit app, local CSV dataset, no
backend.

Core flow: set budget → pick a nutrition goal → (optionally) upload a
menu/meal photo for preview only → app filters the local dataset by budget
→ ranks the remaining meals for the chosen goal → shows one Best Match card
plus up to three alternatives, each with plain-language reasons.

## Tech stack / constraints

- Python, Streamlit, pandas, Pillow, local CSV. Nothing else.
- Explicitly out of scope: React/Next.js, FastAPI, a database, auth,
  Docker, external APIs, external AI APIs, real OCR/image recognition,
  any "complex architecture." Don't reach for these even if they'd be
  the more conventional choice — the constraint is intentional for an
  MVP validation test, not an oversight.

## File structure

- `app.py` — Streamlit entry point. Sidebar (logo, budget selector, goal
  selector, image uploader with simulated-recognition disclaimer, nav) +
  main area (Best Match card, alternative cards, no-results handling).
- `utils/scoring.py` — dataset loading/validation, budget filtering,
  goal-based scoring, ranking, and reason-string generation. Pure
  pandas logic, no Streamlit imports — keep it that way so it stays
  testable outside the UI.
- `utils/ui.py` — Streamlit rendering helpers (CSS injection, card
  layout, Match Score ring, meal image rendering).
- `data/meals.csv` — the local meal dataset (see schema below).
- `assets/meal-placeholder.png` — generic placeholder used for every
  meal's `image` column value in Phase 1.
- `.streamlit/config.toml` — theme (navy text, green accent,
  off-white background) matching `docs/ui-reference.png`.

## Dataset schema (`data/meals.csv`)

Columns: `id, name, price_rm, serving_g, calories, protein_g, carbs_g,
fat_g, image, source`.

- `image` holds a file **path** (currently `assets/meal-placeholder.png`
  for every row in Phase 1) — not an emoji, not inline data. Keep this a
  path so real per-meal photos can be dropped in later without changing
  the schema or the rendering code in `utils/ui.py`.
- `source` must be either `Prototype` or `MyFCD`.
  - `Prototype` = placeholder/estimated values, not verified nutrition
    data. This is what every row currently uses.
  - `MyFCD` = a value verified against the actual Malaysian Food
    Composition Database. **Never** set a row's source to `MyFCD` unless
    the value has actually been checked against MyFCD — don't invent
    data and label it verified. Do not scrape MyFCD.
- Scoring is computed strictly from the numeric columns
  (`price_rm`, `calories`, `protein_g`). There is no free-text `tags`
  column driving recommendations — if you're tempted to add one for
  convenience, don't; it would bypass the numeric-only scoring rule.

## Nutrition goals (fixed set of exactly four)

`High Protein`, `Low Calorie`, `Best Value`, `Balanced` — defined in
`utils/scoring.GOALS`. Don't add goals without updating the weighting
scheme below and the presentation-facing explanation of it.

## Match Score — what it is and isn't

The Match Score (0-100) is a **relative compatibility score** among
meals that already passed the budget filter for the *selected* goal.

It is **not** a health score, a medical rating, or an absolute
nutrition quality rating. Don't let UI copy or reasons drift toward
implying otherwise.

All components are min-max normalized within the budget-filtered set
(so scores answer "how does this compare to what you can actually
afford right now," not "how does this compare to every meal that
exists"):

- `protein_score` — higher `protein_g` is better
- `calorie_score` — lower `calories` is better
- `affordability_score` — lower `price_rm` is better
- `value_score` — higher `protein_g / price_rm` is better

Goal weights:

| Goal | Weights |
|---|---|
| High Protein | 65% protein + 25% affordability + 10% calorie |
| Low Calorie | 65% calorie + 20% protein + 15% affordability |
| Best Value | 70% value + 30% affordability |
| Balanced | 40% protein + 35% calorie + 25% affordability |

Budget filtering happens **before** scoring — an over-budget meal must
never appear, let alone win Best Match.

Reasons shown to the user (`generate_reasons`) only make claims about
the displayed meal's own numbers plus the fixed budget cutoff — no
"highest/lowest among your options" language unless it's genuinely
compared against every affordable meal, not just the top few shown.

## Image upload

The uploader previews the image only. It must never claim the image
was analyzed or that a dish was recognized — the UI copy has to say
plainly that dish recognition is simulated/not implemented in this
version. This is a hard product-honesty requirement, not just a nice-
to-have disclaimer.

## Navigation

Only `Recommendations` and `About` in v0.1. No `History` — there is no
persistence layer to back it, and adding one is out of scope. `About`
is a simple in-page section/expander, not a separate route.

## Known limitations (current phase)

- All nutrition data is `Prototype` (placeholder), not verified MyFCD
  data.
- Meal images are a single shared placeholder graphic, not real photos.
- No persistence — nothing is saved between sessions.
- Dish recognition from uploaded images is not implemented; the
  uploader is preview-only.
