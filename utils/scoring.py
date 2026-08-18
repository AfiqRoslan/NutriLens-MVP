"""Dataset loading, validation, filtering, and scoring for NutriLens.

Match Score definition
-----------------------
The Match Score (0-100) is a RELATIVE COMPATIBILITY SCORE among meals that
have already passed the budget filter. It measures how well a meal fits the
user's SELECTED nutrition goal compared to the other meals they can
currently afford.

It is NOT:
- a health score
- a medical rating
- an absolute nutrition quality rating

Each goal blends up to three min-max normalized components:

- protein_score       : higher protein_g is better
- calorie_score       : lower calories is better
- affordability_score : lower price_rm is better
- value_score         : higher (protein_g / price_rm) is better

Goal weightings:

- High Protein : 65% protein_score + 25% affordability_score + 10% calorie_score
- Low Calorie  : 65% calorie_score + 20% protein_score + 15% affordability_score
- Best Value   : 70% value_score + 30% affordability_score
- Balanced     : 40% protein_score + 35% calorie_score + 25% affordability_score

Normalization is min-max scaling within the set of meals that are already
within budget, so scores answer "how does this compare to the other meals
you can actually afford right now?"
"""

import pandas as pd

GOALS = ["High Protein", "Low Calorie", "Best Value", "Balanced"]

REQUIRED_COLUMNS = [
    "id", "name", "price_rm", "serving_g", "calories",
    "protein_g", "carbs_g", "fat_g", "image", "source",
]

NUMERIC_COLUMNS = ["price_rm", "serving_g", "calories", "protein_g", "carbs_g", "fat_g"]


def load_meals(csv_path):
    """Load the local meal dataset. Raises FileNotFoundError / pandas errors as-is."""
    return pd.read_csv(csv_path)


def validate_meals(df):
    """Validate the dataset structure and values.

    Returns (clean_df, errors, warnings):
    - errors: problems severe enough that the app cannot proceed (missing columns).
    - warnings: individual bad rows that were dropped, so the app can still run.
    """
    errors = []
    warnings = []

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Dataset is missing required column(s): {', '.join(missing_cols)}")
        return df, errors, warnings

    clean = df.copy()

    for col in NUMERIC_COLUMNS:
        clean[col] = pd.to_numeric(clean[col], errors="coerce")

    bad_numeric = clean[NUMERIC_COLUMNS].isna().any(axis=1)
    if bad_numeric.any():
        bad_ids = clean.loc[bad_numeric, "id"].tolist()
        warnings.append(f"Dropped row(s) with non-numeric or missing values: id(s) {bad_ids}")
        clean = clean[~bad_numeric]

    non_positive = clean["price_rm"] <= 0
    if non_positive.any():
        bad_ids = clean.loc[non_positive, "id"].tolist()
        warnings.append(f"Dropped row(s) with price_rm <= 0: id(s) {bad_ids}")
        clean = clean[~non_positive]

    missing_name = clean["name"].isna() | (clean["name"].astype(str).str.strip() == "")
    if missing_name.any():
        bad_ids = clean.loc[missing_name, "id"].tolist()
        warnings.append(f"Dropped row(s) with missing name: id(s) {bad_ids}")
        clean = clean[~missing_name]

    unverified_sources = sorted(set(clean["source"].dropna().unique()) - {"Prototype", "MyFCD"})
    if unverified_sources:
        warnings.append(
            "Dataset contains unrecognized source label(s): "
            f"{unverified_sources}. Expected 'Prototype' or 'MyFCD'."
        )

    return clean.reset_index(drop=True), errors, warnings


def filter_by_budget(df, budget):
    """Remove meals priced above the user's maximum budget."""
    return df[df["price_rm"] <= budget].reset_index(drop=True)


def _normalize(series, higher_is_better=True):
    """Min-max normalize a numeric series to the 0-1 range."""
    min_v, max_v = series.min(), series.max()
    if max_v == min_v:
        return pd.Series(1.0, index=series.index)
    norm = (series - min_v) / (max_v - min_v)
    return norm if higher_is_better else (1 - norm)


def score_meals(df, goal):
    """Add a 'match_score' column (0-100) computed for the given goal.

    See module docstring for the exact weighting per goal.
    """
    scored = df.copy()

    protein_score = _normalize(scored["protein_g"], higher_is_better=True) * 100
    calorie_score = _normalize(scored["calories"], higher_is_better=False) * 100
    affordability_score = _normalize(scored["price_rm"], higher_is_better=False) * 100
    value_score = _normalize(scored["protein_g"] / scored["price_rm"], higher_is_better=True) * 100

    if goal == "High Protein":
        match_score = 0.65 * protein_score + 0.25 * affordability_score + 0.10 * calorie_score
    elif goal == "Low Calorie":
        match_score = 0.65 * calorie_score + 0.20 * protein_score + 0.15 * affordability_score
    elif goal == "Best Value":
        match_score = 0.70 * value_score + 0.30 * affordability_score
    elif goal == "Balanced":
        match_score = 0.40 * protein_score + 0.35 * calorie_score + 0.25 * affordability_score
    else:
        raise ValueError(f"Unknown goal: {goal}")

    scored["match_score"] = match_score.round().astype(int).clip(0, 100)
    return scored


def rank_meals(df, goal, budget, top_n=4):
    """Filter by budget, score by goal, and return the top-N ranked meals.

    Ranking is computed over ALL meals that pass the budget filter, so the
    top result (index 0) is the best match among every affordable option,
    not just among the top_n returned.
    """
    affordable = filter_by_budget(df, budget)
    if affordable.empty:
        return affordable

    scored = score_meals(affordable, goal)
    ranked = scored.sort_values(
        by=["match_score", "price_rm"], ascending=[False, True]
    ).reset_index(drop=True)
    return ranked.head(top_n)


def generate_reasons(row, goal, budget, is_best=False):
    """Build short, transparent reason strings tied directly to the scoring formula.

    Only makes claims about this meal's own numbers (plus the fixed budget
    cutoff) — no comparative claims like "highest" or "lowest", since those
    would require comparing against the full affordable set rather than
    just the displayed row.
    """
    reasons = [f"Within your RM{budget:g} budget"]

    if goal == "High Protein":
        reasons.append(f"Provides {row['protein_g']:.0f}g protein")
        reasons.append("Strong protein match")
    elif goal == "Low Calorie":
        reasons.append(f"{row['calories']:.0f} kcal per serving")
        reasons.append("Lower-calorie match")
    elif goal == "Best Value":
        value = row["protein_g"] / row["price_rm"]
        reasons.append(f"{value:.1f}g protein per RM")
        reasons.append("Strong protein-for-price value")
    elif goal == "Balanced":
        reasons.append(f"{row['protein_g']:.0f}g protein and {row['calories']:.0f} kcal")
        reasons.append("Balances protein, calories and price")

    if is_best:
        reasons.append(f"Best match for {goal}")

    return reasons


def search_meal_names(df):
    """Return a sorted, de-duplicated list of meal names for a search/select widget."""
    return sorted(df["name"].dropna().unique().tolist())


def evaluate_selected_meal(df, meal_name, goal, budget):
    """Look up a meal by name and evaluate it against the goal/budget.

    This is the single pathway a selected meal should go through to get its
    nutrition info and goal-based evaluation, regardless of how it was
    identified — manual search today, potentially image recognition later.
    Reuses filter_by_budget/score_meals/generate_reasons unmodified, so the
    Match Score formula and the budget-before-scoring rule stay untouched;
    an over-budget meal is never scored.

    Returns None if meal_name isn't in df, otherwise a dict:
    {"meal": Series, "in_budget": bool, "match_score": int|None, "reasons": list|None}
    """
    matches = df[df["name"] == meal_name]
    if matches.empty:
        return None

    meal = matches.iloc[0]
    affordable = filter_by_budget(df, budget)
    in_budget = bool((affordable["id"] == meal["id"]).any())

    match_score = None
    reasons = None
    if in_budget:
        scored = score_meals(affordable, goal)
        meal = scored.loc[scored["id"] == meal["id"]].iloc[0]
        match_score = int(meal["match_score"])
        reasons = generate_reasons(meal, goal, budget, is_best=False)

    return {
        "meal": meal,
        "in_budget": in_budget,
        "match_score": match_score,
        "reasons": reasons,
    }
