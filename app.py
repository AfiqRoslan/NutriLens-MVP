"""NutriLens MVP — Streamlit entry point.

Sidebar collects Budget + Nutrition Goal + an optional (preview-only) image
upload. Main area shows the ranked Best Match + up to three alternatives,
computed from utils/scoring.py and rendered with utils/ui.py.
"""

import os

import streamlit as st

from utils import scoring, ui

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(APP_DIR, "data", "meals.csv")
LOGO_PATH = os.path.join(APP_DIR, "assets", "nutrilens-logo.png")

BUDGET_OPTIONS = [6, 8, 10, 12, 15, 18, 20, 25]

st.set_page_config(page_title="NutriLens", page_icon="🥗", layout="wide")
ui.inject_css()


@st.cache_data
def get_dataset():
    """Load and validate the meal dataset.

    Returns (clean_df, errors, warnings). clean_df is None when the CSV
    itself could not be read (missing file, malformed CSV, etc.) — that
    failure is surfaced as an entry in `errors` rather than raising, so
    the app can show a friendly message instead of a raw traceback.
    """
    try:
        df = scoring.load_meals(DATA_PATH)
    except FileNotFoundError:
        return None, [f"Meal dataset not found at: {DATA_PATH}"], []
    except Exception as exc:
        return None, [f"Could not read the meal dataset ({type(exc).__name__}): {exc}"], []

    clean, errors, warnings = scoring.validate_meals(df)
    return clean, errors, warnings


def render_recommendations(clean_df, budget, goal):
    st.title("Your Best Match")

    ranked = scoring.rank_meals(clean_df, goal, budget, top_n=4)

    if ranked.empty:
        st.warning(
            f"No meals found within RM{budget:g}. "
            "Try increasing your budget to see recommendations."
        )
        cheapest = clean_df.sort_values("price_rm").head(1)
        if not cheapest.empty:
            cheapest_price = cheapest.iloc[0]["price_rm"]
            st.caption(f"The cheapest meal in our dataset is RM{cheapest_price:.2f}.")
        return

    best = ranked.iloc[0]
    best_reasons = scoring.generate_reasons(best, goal, budget, is_best=True)
    ui.render_best_match_card(best, best_reasons)

    alternatives = ranked.iloc[1:]
    if not alternatives.empty:
        st.subheader("Other options")
        for _, row in alternatives.iterrows():
            reasons = scoring.generate_reasons(row, goal, budget, is_best=False)
            ui.render_alt_card(row, reasons)

    st.caption(
        "Match Score reflects compatibility with your selected goal among meals "
        "within your budget — it is not a health or medical rating."
    )


def render_about():
    st.title("About NutriLens")
    st.markdown(
        """
        NutriLens helps budget-conscious students decide what to order by
        weighing both **price** and a **nutrition goal** before they buy.

        **How recommendations work:** meals priced above your selected budget
        are removed first. The remaining meals are ranked with a Match Score
        (0-100) built from your meal's protein, calories, and price — the
        exact weighting depends on the goal you pick. The score is a
        relative compatibility measure among meals you can currently afford,
        not a health or medical rating.
        """
    )
    with st.expander("Data & limitations in this prototype"):
        st.markdown(
            """
            - Nutrition values in this version are **placeholder/prototype**
              estimates, not verified against an official food composition
              database.
            - Meal photos are a shared placeholder graphic, not real photos
              of each dish.
            - Uploading a menu or meal photo previews the image only —
              **automatic dish recognition is simulated and not implemented**
              in this version. No image analysis is performed.
            - Nothing is saved between sessions.
            """
        )


def render_sidebar():
    with st.sidebar.container(border=True, key="nl-sidebar-logo-card"):
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, use_container_width=True)
        else:
            st.title("NutriLens")

    st.sidebar.markdown("### Preferences")

    budget_labels = [f"RM{b}" for b in BUDGET_OPTIONS]
    budget_choice = st.sidebar.selectbox("Budget", budget_labels, index=2)
    budget = float(budget_choice.replace("RM", ""))

    goal = st.sidebar.selectbox("Goal", scoring.GOALS)

    st.sidebar.markdown("### Upload menu or meal image (optional)")
    uploaded_file = st.sidebar.file_uploader(
        "PNG or JPG", type=["png", "jpg", "jpeg"], label_visibility="collapsed"
    )
    if uploaded_file is not None:
        st.sidebar.image(uploaded_file, use_container_width=True)
    st.sidebar.info(
        "Dish recognition is simulated — your image is previewed only, not analyzed.",
        icon="ℹ️",
    )

    st.sidebar.markdown("---")
    nav = st.sidebar.radio("Navigate", ["Recommendations", "About"], label_visibility="collapsed")

    return budget, goal, nav


def main():
    clean_df, errors, warnings = get_dataset()

    if errors:
        st.error("The meal dataset could not be loaded:")
        for err in errors:
            st.error(err)
        st.stop()

    budget, goal, nav = render_sidebar()

    if warnings:
        with st.sidebar.expander("Dataset warnings"):
            for warn in warnings:
                st.caption(warn)

    if nav == "Recommendations":
        render_recommendations(clean_df, budget, goal)
    else:
        render_about()


if __name__ == "__main__":
    main()
