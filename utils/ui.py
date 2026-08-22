"""Streamlit rendering helpers for NutriLens: CSS injection, cards, and the Match Score ring."""

import html
import os

import streamlit as st

NAVY = "#1B2A41"
GREEN = "#4B8B5C"
GREEN_LIGHT = "#EAF3EC"
CARD_BG = "#FFFFFF"
RING_TRACK = "#E4E9E6"


def inject_css():
    """Inject the shared layout / card / ring / typography styles used across the app."""
    st.markdown(
        f"""
        <style>
        .block-container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        .st-key-nl-best-match-card {{
            border-radius: 16px !important;
            box-shadow: 0 2px 10px rgba(27, 42, 65, 0.08) !important;
            padding: 1.25rem 1.5rem !important;
            margin-bottom: 1rem !important;
        }}
        [class*="st-key-nl-alt-card-"] {{
            border-radius: 14px !important;
            box-shadow: 0 2px 10px rgba(27, 42, 65, 0.06) !important;
            padding: 1rem 1.25rem !important;
            margin-bottom: 0.75rem !important;
        }}
        .st-key-nl-selected-meal-card {{
            border-radius: 14px !important;
            box-shadow: 0 2px 10px rgba(27, 42, 65, 0.06) !important;
            padding: 1rem 1.25rem !important;
            margin-bottom: 1rem !important;
        }}
        .st-key-nl-sidebar-logo-card {{
            border-radius: 14px !important;
            padding: 1rem !important;
            margin-bottom: 1rem !important;
        }}
        [data-testid="stAlert"] {{
            padding: 0.6rem 0.9rem;
        }}
        .nl-badge {{
            display: inline-block;
            background: {GREEN};
            color: white;
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.2rem 0.7rem;
            border-radius: 999px;
            margin-bottom: 0.5rem;
        }}
        .nl-meal-name {{
            color: {NAVY};
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0.2rem 0;
        }}
        .nl-meal-name-sm {{
            color: {NAVY};
            font-size: 1.05rem;
            font-weight: 600;
            margin: 0.1rem 0;
        }}
        .nl-meal-meta {{
            color: #5A6B7A;
            font-size: 1rem;
            margin-bottom: 0.4rem;
        }}
        .nl-meal-meta-sm {{
            color: #5A6B7A;
            font-size: 0.92rem;
            margin-bottom: 0.4rem;
        }}
        .nl-reason {{
            color: {NAVY};
            font-size: 0.9rem;
            margin: 0.15rem 0;
        }}
        .nl-ring-wrap {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .nl-placeholder-img {{
            background: {GREEN_LIGHT};
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #8FA89A;
            font-size: 0.8rem;
            text-align: center;
            padding: 0.5rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_score_ring(score, size=88):
    """Return an HTML snippet for a circular Match Score gauge (0-100)."""
    score = max(0, min(100, int(score)))
    return f"""
    <div class="nl-ring-wrap">
        <div style="
            width: {size}px; height: {size}px; border-radius: 50%;
            background: conic-gradient({GREEN} {score * 3.6}deg, {RING_TRACK} 0deg);
            display: flex; align-items: center; justify-content: center;
        ">
            <div style="
                width: {size - 16}px; height: {size - 16}px; border-radius: 50%;
                background: {CARD_BG}; display: flex; flex-direction: column;
                align-items: center; justify-content: center;
            ">
                <span style="font-size: 1.1rem; font-weight: 700; color: {NAVY};">{score}</span>
                <span style="font-size: 0.65rem; color: #8896A3;">/100</span>
            </div>
        </div>
    </div>
    """


def render_meal_image(image_path, width="stretch"):
    """Render a meal image responsively inside its card column.

    Using the column width keeps meal photos prominent on desktop while
    allowing them to shrink naturally on narrower screens.
    """
    if image_path and os.path.exists(image_path):
        st.image(image_path, width=width)
    else:
        st.markdown(
            '<div class="nl-placeholder-img" style="width:100%;aspect-ratio:4/3;">Image not available</div>',
            unsafe_allow_html=True,
        )


def _render_poultry_unverified_note(poultry_status):
    """Lightweight, non-medical status line — the one currently supported case.

    'contains' is intentionally not rendered here: scoring.py already filters
    those rows out of ranked results whenever the poultry filter is active, so
    a ranked card should never carry that status while this note is shown (the
    selected-meal card handles 'contains' explicitly, with its own message,
    since it can bypass filtering). 'does_not_contain' has no current records,
    so no wording is invented for it yet.
    """
    if poultry_status == "unknown":
        st.caption("⚠ Poultry status unverified")


def render_best_match_card(row, reasons, show_poultry_status=False):
    """Render the large Best Match card: image, name/macros, score ring, reasons.

    Uses st.container(border=True, key=...) as the actual nesting mechanism so
    the columns/image/text below genuinely render inside one bordered/shadowed
    card. Image and ring use fixed pixel sizes tuned to the card's own width
    (not the full unconstrained viewport) so the image roughly matches the
    height of the text block and the ring sits close to it.
    """
    meal_name = html.escape(str(row["name"]))

    with st.container(border=True, key="nl-best-match-card"):
        st.markdown('<span class="nl-badge">★ Best Match</span>', unsafe_allow_html=True)

        img_col, info_col, ring_col = st.columns([1.4, 3, 1])
        with img_col:
            render_meal_image(row["image"])
        with info_col:
            st.markdown(f'<div class="nl-meal-name">{meal_name}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="nl-meal-meta">RM{row["price_rm"]:.2f} &nbsp;|&nbsp; '
                f'{row["calories"]:.0f} kcal &nbsp;|&nbsp; {row["protein_g"]:.0f}g protein</div>',
                unsafe_allow_html=True,
            )
            if show_poultry_status:
                _render_poultry_unverified_note(row["poultry_status"])
            for reason in reasons:
                safe_reason = html.escape(str(reason))
                st.markdown(f'<div class="nl-reason">✅ {safe_reason}</div>', unsafe_allow_html=True)
        with ring_col:
            st.markdown(render_score_ring(row["match_score"], size=104), unsafe_allow_html=True)


def render_selected_meal_card(
    evaluation,
    is_best_match=False,
    show_poultry_status=False,
):
    """Render the meal a user found via manual search.

    Shows full nutrition facts (price, calories, protein, carbs, fat) plus a
    goal evaluation reusing the same reasons/ring as the ranked cards. Gated
    on evaluation["is_eligible"] (budget AND poultry filter), not just
    in_budget alone -- an in-budget meal can still be is_eligible=False when
    the poultry filter is active and poultry_status == "contains", in which
    case reasons/match_score are None and must not be iterated/rendered.
    Reuses the existing container/CSS pattern rather than introducing new
    styling. When this meal is also the current Best Match, the caller skips
    rendering a separate Best Match card and passes is_best_match=True so the
    badge communicates that instead of duplicating the meal.
    """
    meal = evaluation["meal"]
    meal_name = html.escape(str(meal["name"]))
    badge_text = "\U0001F50D Selected Meal \u2022 \u2B50 Best Match" if is_best_match else "\U0001F50D Selected Meal"

    with st.container(border=True, key="nl-selected-meal-card"):
        st.markdown(f'<span class="nl-badge">{badge_text}</span>', unsafe_allow_html=True)

        img_col, info_col, ring_col = st.columns([1.3, 3, 1])
        with img_col:
            render_meal_image(meal["image"])
        with info_col:
            st.markdown(f'<div class="nl-meal-name-sm">{meal_name}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="nl-meal-meta-sm">RM{meal["price_rm"]:.2f} &nbsp;|&nbsp; '
                f'{meal["calories"]:.0f} kcal &nbsp;|&nbsp; {meal["protein_g"]:.0f}g protein '
                f'&nbsp;|&nbsp; {meal["carbs_g"]:.0f}g carbs &nbsp;|&nbsp; {meal["fat_g"]:.0f}g fat</div>',
                unsafe_allow_html=True,
            )

            if not evaluation["in_budget"]:
                st.markdown(
                    '<div class="nl-reason">This meal is above your current budget, '
                    'so it was not scored against your goal.</div>',
                    unsafe_allow_html=True,
                )
                if show_poultry_status and meal["poultry_status"] == "unknown":
                    _render_poultry_unverified_note(meal["poultry_status"])
            elif evaluation["is_eligible"]:
                for reason in evaluation["reasons"]:
                    safe_reason = html.escape(str(reason))
                    st.markdown(f'<div class="nl-reason">\u2705 {safe_reason}</div>', unsafe_allow_html=True)
                if show_poultry_status and meal["poultry_status"] == "unknown":
                    _render_poultry_unverified_note(meal["poultry_status"])
            else:
                st.caption("Contains poultry (prototype data)")
                st.markdown(
                    '<div class="nl-reason">Known to contain poultry in this prototype '
                    'dataset, so it is excluded from your recommendations.</div>',
                    unsafe_allow_html=True,
                )
        with ring_col:
            if evaluation["is_eligible"]:
                st.markdown(render_score_ring(evaluation["match_score"]), unsafe_allow_html=True)


def render_alt_card(row, reasons, show_poultry_status=False):
    """Render a compact alternative meal card with a collapsible reasons section.

    Each alt card gets a unique container key (derived from the meal id) since
    Streamlit requires distinct keys per container within a single run. Image
    and ring are small fixed sizes so the row height is driven by the text
    content, not by an oversized image. Uses the smaller `.nl-meal-meta-sm`
    typography variant (distinct from the Best Match card's `.nl-meal-meta`)
    so the step 7 typography bump doesn't re-inflate this card's compactness.
    """
    meal_name = html.escape(str(row["name"]))

    with st.container(border=True, key=f"nl-alt-card-{row['id']}"):
        img_col, info_col, ring_col = st.columns([0.9, 3.4, 0.8])
        with img_col:
            render_meal_image(row["image"])
        with info_col:
            st.markdown(f'<div class="nl-meal-name-sm">{meal_name}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="nl-meal-meta-sm">RM{row["price_rm"]:.2f} &nbsp;|&nbsp; '
                f'{row["calories"]:.0f} kcal &nbsp;|&nbsp; {row["protein_g"]:.0f}g protein</div>',
                unsafe_allow_html=True,
            )
            if show_poultry_status and row["poultry_status"] == "unknown":
                _render_poultry_unverified_note(row["poultry_status"])
            with st.expander("Why this meal?"):
                for reason in reasons:
                    safe_reason = html.escape(str(reason))
                    st.markdown(f'<div class="nl-reason">✅ {safe_reason}</div>', unsafe_allow_html=True)
        with ring_col:
            st.markdown(render_score_ring(row["match_score"], size=72), unsafe_allow_html=True)
