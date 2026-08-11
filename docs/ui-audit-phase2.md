# Phase 2 UI/UX Audit

Comparison of all current implementation screenshots (`docs/current-ui-01-full.png`
through `docs/current-ui-06-about.png`, captured on an ultrawide display) against
`docs/ui-reference.png`, the target design. This is an audit only — no files have
been modified. Findings are grounded in `app.py` and `utils/ui.py` as they existed
at the start of Phase 2.

Two of the originally suspected issues — "Best Match elements do not visually form
one cohesive card" and "unexplained blank rounded bars appear around/between
cards" — turned out to share a single root cause and are written up together as
one structural finding (#2) rather than two.

---

### 1. No max-width constraint on the main content area
**CURRENT**: `layout="wide"` (`app.py:20`) with no CSS ceiling on `.block-container`. On the ultrawide capture, the content region is ~1900px wide with nothing capping it, so every downstream column ratio (`st.columns([1,2,1])`, `[1,3,1])`) computes against that huge width instead of a sane reading width.
**TARGET**: The reference keeps a bounded content column — cards, rings, and text sit at a comfortable, readable width regardless of screen size; it never stretches edge-to-edge.
**RECOMMENDED FIX**: In `inject_css()`, add a rule targeting Streamlit's block-container (e.g. `.block-container { max-width: 1100px; margin: 0 auto; }`). This is the root fix that most other symptoms below inherit from — everything downstream should be re-measured after this lands.
**FILE**: `utils/ui.py`
**PRIORITY**: Critical structural

---

### 2. Card "container" div is opened and closed across separate `st.markdown()` calls, so it never actually wraps its content
**CURRENT**: `render_best_match_card`/`render_alt_card` (`utils/ui.py:120-169`) call `st.markdown('<div class="nl-card">', unsafe_allow_html=True)`, then run `st.columns(...)`/`st.image`/more `st.markdown` calls, then close with a separate `st.markdown('</div>', unsafe_allow_html=True)`. In Streamlit, each `st.markdown()` call renders into its **own** isolated element block — it does not nest the widgets that come after it inside that div. The practical effect, visible in the screenshots: the real card content (image, name, ring) has no visible border/shadow around it at all (screenshot 02 — text and ring just float on white), while the orphaned opening `<div class="nl-card">` tag renders on its own as an *empty* rounded, bordered, shadowed box (padding + border + box-shadow with nothing inside) — that's exactly the "unexplained blank rounded bars" appearing above/between cards in screenshots 01, 03, 04.
**TARGET**: Each meal is one cohesive bordered/shadowed card — image, text, and score ring all visually contained together, no stray empty boxes.
**RECOMMENDED FIX**: Replace the manual div-open/div-close pattern with `st.container(border=True, key="...")` as the actual nesting mechanism (Streamlit's container is a real context manager, so content placed inside it — columns, image, markdown — genuinely nests in the DOM). Use the container's `key` to get a stable CSS class (`st-key-<key>`) and style border-radius/padding/shadow on that via `inject_css()`, instead of hand-rolled `<div>` tags.
**FILE**: `utils/ui.py`
**PRIORITY**: Critical structural

---

### 3. Best Match food image is oversized
**CURRENT**: `img_col` gets 1 of 4 column-width units (`st.columns([1, 2, 1])`, `utils/ui.py:127`) inside an unconstrained ~1900px row, and `render_meal_image` (`utils/ui.py:108-117`) calls `st.image(..., use_container_width=True)` against a `.nl-placeholder-img` with `aspect-ratio: 1/1`. The result (screenshot 02) is a ~470px square image — roughly 2.5x the height of the entire text block beside it.
**TARGET**: The food photo is modestly sized, roughly matching the height of the name/macros/checkmarks block next to it — image and text read as one balanced row.
**RECOMMENDED FIX**: Cap the image at a fixed pixel size (e.g. ~220-260px) rather than letting it scale to whatever the column happens to be, and re-tune the column ratio once the max-width fix (#1) is in place.
**FILE**: `utils/ui.py`
**PRIORITY**: High

---

### 4. Alternative cards are tall vertical blocks instead of compact horizontal rows
**CURRENT**: Same oversized-image mechanism as #3 applies to `render_alt_card` (`st.columns([1, 3, 1])`, `utils/ui.py:152`). Screenshots 03/04 show each alternative as a ~380px-tall card with a ~350px placeholder image and a large empty white gap below the two lines of text and the expander.
**TARGET**: Each alternative is a slim horizontal row (~90-100px tall) — small thumbnail, name/price/macros, small ring, all on one line, tightly packed, with a chevron to expand details.
**RECOMMENDED FIX**: Give the alt-card thumbnail a small fixed size (e.g. ~72-90px square) instead of scaling with the column, and reduce the card's vertical padding so row height is driven by content, not by an oversized image.
**FILE**: `utils/ui.py`
**PRIORITY**: High

---

### 5. Match Score ring is visually disconnected from the meal info
**CURRENT**: `ring_col` (`utils/ui.py:127, 152`) receives a fixed fraction of an unconstrained-width row, so the 88px ring (`render_score_ring`, `utils/ui.py:85`) ends up stranded far to the right with a huge dead-space gap between it and the text block (clearly visible in screenshot 01/03 — text ends around x≈830px, ring sits at x≈1730px).
**TARGET**: The ring sits immediately adjacent to the meal text, reading as part of the same information cluster, not a separate floating element.
**RECOMMENDED FIX**: Mostly resolved as a side effect of the max-width fix (#1) plus tighter column ratios from #3/#4; additionally consider a slightly larger ring (~100-110px) so it reads with appropriate visual weight at the new, more compact card width.
**FILE**: `utils/ui.py`
**PRIORITY**: High

---

### 6. Prototype disclaimer occupies too much sidebar height
**CURRENT**: The sidebar `st.info(...)` block (`app.py:128-133`) is a 6-line paragraph, and screenshot 05 shows it consuming roughly a third of the entire visible sidebar height above the fold.
**TARGET**: The equivalent note in the reference is 1-2 short lines in a compact tinted box.
**RECOMMENDED FIX**: Shorten the copy while preserving the required substance (image is previewed only, not analyzed, recommendations come from Budget/Goal) — e.g. "Dish recognition is simulated — your image is previewed only, not analyzed." Optionally also tighten `st.info`'s default internal padding via CSS targeting the alert container.
**FILE**: `app.py` (copy), `utils/ui.py` (optional padding tightening)
**PRIORITY**: Medium

---

### 7. Typography is undersized relative to the page
**CURRENT**: Card typography is set at 0.9-1.3rem (`.nl-meal-name`, `.nl-meal-meta`, `.nl-reason`, `utils/ui.py:38-58`) — sized as if the surrounding container were already a normal reading width. Against the current ultrawide, unconstrained layout, this reads as noticeably small.
**TARGET**: Headings and card text are proportionally bolder/larger relative to the card and page.
**RECOMMENDED FIX**: Re-evaluate after the max-width fix (#1) — much of this is a relative-scale illusion that self-corrects once content isn't spread across the full viewport. On top of that, bump the meal name and price/macro line a step (e.g. name 1.3rem→1.5rem, meta 0.92rem→1rem) to match the reference's weight.
**FILE**: `utils/ui.py`
**PRIORITY**: Medium

---

### 8. Sidebar proportions and About-page density
**CURRENT**: The logo (`app.py:109-110`) sits directly on the sidebar's flat secondary background with no visual separation, unlike the reference's white card treatment around the logo. Separately, the About page (screenshot 06, `app.py:77-105`) reads sparse mainly because — like everything else — it inherits the unconstrained width; two short paragraphs and one expander stretched across ~1900px look thin.
**TARGET**: Reference sidebar gives the logo a distinct white card at the top before "Preferences" begins. About page content sits in a bounded, readable column.
**RECOMMENDED FIX**: About-page sparseness is expected to mostly resolve once the max-width fix (#1) lands — verify visually before adding anything. Separately, wrap the sidebar logo in a small white rounded container (`st.container(border=True)`) to match the reference's card treatment.
**FILE**: `app.py`, `utils/ui.py`
**PRIORITY**: Low

---

## Proposed order of implementation

1. **Max-width constraint** (#1) — foundational; every other fix should be measured against the corrected layout, not the current ultrawide-stretched one.
2. **Card container restructure to `st.container(border=True)`** (#2) — structural, must land before resizing images/rings since it changes how columns nest.
3. **Best Match image sizing + column ratio** (#3)
4. **Alternative card thumbnail sizing + row compactness** (#4)
5. **Match Score ring column tightening / size bump** (#5)
6. **Sidebar disclaimer copy + padding** (#6)
7. **Typography scale pass** (#7) — re-evaluate against the now-corrected layout before changing values
8. **Sidebar logo card + About-page density check** (#8) — final polish pass, confirming what #1 already fixed and only patching what's left

## Implementation constraints (carried over from the audit request)

Do NOT change: `utils/scoring.py`, `data/meals.csv`, scoring weights, budget filtering,
Match Score calculations, recommendation logic, image-upload behaviour.

Do NOT add: JavaScript, React, external CSS frameworks, frontend libraries, new
Python dependencies.

Prefer: Streamlit columns, Streamlit containers, controlled CSS, max-width
constraints, responsive sizing.
