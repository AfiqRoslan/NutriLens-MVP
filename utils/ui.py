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


def render_meal_image(image_path, size=220):
    """Render a meal image at a fixed pixel size if the file exists, otherwise a
    neutral placeholder box at the same fixed size.

    Fixed-size (rather than use_container_width) so image size is controlled
    explicitly per card type instead of stretching to whatever column width
    an unconstrained row happens to produce. Kept path-based (rather than
    emoji/inline data) so real per-meal photos can be dropped in later
    without changing this function or the CSV schema.
    """
    if image_path and os.path.exists(image_path):
        st.image(image_path, width=size)
    else:
        st.markdown(
            f'<div class="nl-placeholder-img" style="width:{size}px;height:{size}px;">Image not available</div>',
            unsafe_allow_html=True,
        )


def render_best_match_card(row, reasons):
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

        img_col, info_col, ring_col = st.columns([1, 3, 1])
        with img_col:
            render_meal_image(row["image"], size=200)
        with info_col:
            st.markdown(f'<div class="nl-meal-name">{meal_name}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="nl-meal-meta">RM{row["price_rm"]:.2f} &nbsp;|&nbsp; '
                f'{row["calories"]:.0f} kcal &nbsp;|&nbsp; {row["protein_g"]:.0f}g protein</div>',
                unsafe_allow_html=True,
            )
            for reason in reasons:
                safe_reason = html.escape(str(reason))
                st.markdown(f'<div class="nl-reason">✅ {safe_reason}</div>', unsafe_allow_html=True)
        with ring_col:
            st.markdown(render_score_ring(row["match_score"], size=104), unsafe_allow_html=True)


def render_alt_card(row, reasons):
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
        img_col, info_col, ring_col = st.columns([1, 3, 1])
        with img_col:
            render_meal_image(row["image"], size=72)
        with info_col:
            st.markdown(f'<div class="nl-meal-name-sm">{meal_name}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="nl-meal-meta-sm">RM{row["price_rm"]:.2f} &nbsp;|&nbsp; '
                f'{row["calories"]:.0f} kcal &nbsp;|&nbsp; {row["protein_g"]:.0f}g protein</div>',
                unsafe_allow_html=True,
            )
            with st.expander("Why this meal?"):
                for reason in reasons:
                    safe_reason = html.escape(str(reason))
                    st.markdown(f'<div class="nl-reason">✅ {safe_reason}</div>', unsafe_allow_html=True)
        with ring_col:
            st.markdown(render_score_ring(row["match_score"], size=72), unsafe_allow_html=True)
