import streamlit as st
import pandas as pd
import os
import re

# ════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="MMCOE Teacher Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# DATA LAYER

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timetable_data.csv")

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
REQUIRED_COLS = ["professor", "day", "time_slot", "division", "subject", "room", "type"]

PLACEHOLDER_PROF = "Select professor"
PLACEHOLDER_DAY = "Select day"
PLACEHOLDER_TIME = "Select time"


def _time_sort_key(t: str):
    m = re.search(r"(\d{1,2}):(\d{2})\s*([ap]m)?", str(t).lower())
    if not m:
        return (99, 99)
    hour, minute, meridian = int(m.group(1)), int(m.group(2)), m.group(3)
    if meridian == "pm" and hour != 12:
        hour += 12
    elif meridian == "am" and hour == 12:
        hour = 0
    return (hour, minute)


@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    try:
        if not os.path.exists(path):
            return pd.DataFrame(columns=REQUIRED_COLS)
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    except Exception:
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="latin-1")
        except Exception:
            return pd.DataFrame(columns=REQUIRED_COLS)

    for col in REQUIRED_COLS:
        if col not in df.columns:
            df[col] = ""

    for col in REQUIRED_COLS:
        df[col] = df[col].astype(str).str.strip()

    df = df[(df["professor"] != "") & (df["day"] != "") & (df["time_slot"] != "")]
    return df.reset_index(drop=True)


df = load_data(CSV_PATH)
DATA_OK = not df.empty

if DATA_OK:
    all_professors = sorted(df["professor"].unique().tolist())
else:
    all_professors = []


def escape_html(text: str) -> str:
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _days_for_professor(prof: str) -> list[str]:
    if prof == PLACEHOLDER_PROF:
        return []
    subset = df[df["professor"] == prof]
    return [d for d in DAY_ORDER if d in subset["day"].unique()]


def _times_for_professor_day(prof: str, day: str) -> list[str]:
    if prof == PLACEHOLDER_PROF or day == PLACEHOLDER_DAY:
        return []
    subset = df[(df["professor"] == prof) & (df["day"] == day)]
    return sorted(subset["time_slot"].unique().tolist(), key=_time_sort_key)


def _ensure_option(key: str, options: list[str], default: str) -> None:
    if st.session_state.get(key) not in options:
        st.session_state[key] = default


def _on_professor_change() -> None:
    st.session_state["day_select"] = PLACEHOLDER_DAY
    st.session_state["time_select"] = PLACEHOLDER_TIME


def _on_day_change() -> None:
    st.session_state["time_select"] = PLACEHOLDER_TIME


# ════════════════════════════════════════════════════════════════════════════
# STYLES
# ════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap');

:root {
    --maroon-950: #260606;
    --maroon-900: #3D0A0A;
    --maroon-800: #5C0F0F;
    --crimson-2:  #A8161B;
    --gold:       #C9A24B;
    --gold-2:     #DEC07E;
    --paper:      #FBF9F7;
    --paper-2:    #F4EFEC;
    --line:       #E7DEDA;
    --ink:        #1A1110;
    --ink-soft:   #5A4642;
    --ink-faint:  #8C7975;
    --white:      #FFFFFF;
    --ease:       cubic-bezier(.16,1,.3,1);
    --ease-smooth: cubic-bezier(.22,1,.36,1);
    --ease-spring: cubic-bezier(.34,1.56,.64,1);
}

* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif;
    color: var(--ink);
    -webkit-font-smoothing: antialiased;
}

.stApp {
    background:
        radial-gradient(900px 400px at 100% 0%, rgba(142,18,18,0.05), transparent 55%),
        radial-gradient(700px 400px at 0% 0%, rgba(201,162,75,0.05), transparent 50%),
        var(--paper) !important;
}

#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }

.block-container {
    padding: 0 1.25rem 2.5rem 1.25rem !important;
    max-width: 1100px;
}

section.main, section.main > div, [data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stHorizontalBlock"] {
    overflow: visible !important;
    transform: none !important;
}

*:focus-visible { outline: 2px solid var(--crimson-2); outline-offset: 2px; }
::selection { background: rgba(168,22,27,0.15); }

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes chipIn {
    from { opacity: 0; transform: scale(0.96); }
    to   { opacity: 1; transform: scale(1); }
}

/* ── Hero ── */
.hero {
    background: linear-gradient(160deg, var(--maroon-900) 0%, var(--maroon-950) 100%);
    margin: 0 -1.25rem 2rem -1.25rem;
    border-bottom: 1px solid rgba(201,162,75,0.25);
    animation: fadeUp 0.5s var(--ease) both;
}
.hero-inner {
    padding: clamp(1.75rem, 5vw, 3rem) clamp(1.25rem, 4vw, 2.5rem);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.5rem;
    flex-wrap: wrap;
}
.hero-brand { display: flex; align-items: center; gap: 1rem; min-width: 0; }
.hero-crest {
    width: clamp(52px, 10vw, 64px);
    height: clamp(52px, 10vw, 64px);
    flex-shrink: 0;
    border-radius: 16px;
    background: linear-gradient(150deg, var(--crimson-2), var(--maroon-800));
    border: 1px solid rgba(201,162,75,0.45);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem;
}
.hero-eyebrow {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.2em;
    text-transform: uppercase; color: var(--gold); margin-bottom: 0.4rem;
}
.hero-title {
    font-family: 'Fraunces', serif;
    font-size: clamp(1.6rem, 4.5vw, 2.4rem);
    font-weight: 700; color: #FBF6EE; line-height: 1.1;
    margin: 0 0 0.45rem 0;
}
.hero-title em { font-style: italic; font-weight: 400; color: rgba(255,222,222,0.9); }
.hero-sub {
    font-size: clamp(0.82rem, 2.5vw, 0.92rem);
    color: rgba(255,255,255,0.58); line-height: 1.5;
    max-width: 520px;
}
.hero-stats {
    display: flex; gap: 1.25rem; flex-shrink: 0;
}
.hero-stat { text-align: center; min-width: 64px; }
.hero-stat .num {
    font-family: 'Fraunces', serif;
    font-size: 1.4rem; font-weight: 700; color: var(--gold-2);
}
.hero-stat .lbl {
    font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: rgba(255,255,255,0.45); margin-top: 0.2rem;
}

/* ── Panel (Streamlit bordered container) ── */
[data-testid="stVerticalBlockBorderWrapper"]:has(.panel-head) {
    background: var(--white) !important;
    border: 1px solid var(--line) !important;
    border-radius: 20px !important;
    box-shadow: 0 16px 40px -24px rgba(43,7,7,0.35) !important;
    padding: 1.5rem 1.75rem 1.25rem 1.75rem !important;
    margin-bottom: 1.25rem !important;
    overflow: visible !important;
    transform: none !important;
    animation: fadeIn 0.4s var(--ease-smooth) 0.05s both;
}
.panel-head {
    display: flex; align-items: baseline; justify-content: space-between;
    margin-bottom: 1.25rem; padding-bottom: 1rem;
    border-bottom: 1px solid var(--paper-2); gap: 0.75rem; flex-wrap: wrap;
}
.panel-title {
    font-family: 'Fraunces', serif; font-size: 1.25rem; font-weight: 600;
    color: var(--maroon-900);
}
.panel-kicker { font-size: 0.72rem; color: var(--ink-faint); font-weight: 500; }

.field-label {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--crimson-2); margin-bottom: 0.4rem;
    transition: color 0.3s var(--ease-smooth);
}
.field-label.filled { color: #1C7740; }
.field-label.muted { color: var(--ink-faint); }
.field-hint {
    font-size: 0.72rem; color: var(--ink-faint); margin-top: 0.35rem; line-height: 1.4;
}

/* ── Selectbox — selected value must stay visible in the closed bar ── */
div[data-testid="stSelectbox"] label { display: none !important; }
div[data-testid="stSelectbox"] {
    margin-bottom: 0 !important;
    position: relative !important;
    z-index: 1 !important;
}
div[data-testid="stSelectbox"]:has([aria-expanded="true"]) {
    z-index: 100 !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    border: 1.5px solid var(--line) !important;
    border-radius: 12px !important;
    background: var(--white) !important;
    min-height: 46px !important;
    transition:
        border-color 0.25s var(--ease-smooth),
        box-shadow 0.25s var(--ease-smooth),
        background-color 0.25s var(--ease-smooth) !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover {
    border-color: #D4B4B4 !important;
    background: var(--paper) !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within > div,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div[aria-expanded="true"] {
    border-color: var(--crimson-2) !important;
    box-shadow: 0 0 0 3px rgba(168,22,27,0.12) !important;
    background: var(--white) !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"].is-selected > div {
    border-color: #E8C4C4 !important;
    background: #FFFBFB !important;
}

/* Force legible text in the closed control — every BaseWeb layer */
div[data-testid="stSelectbox"] div[data-baseweb="select"] div,
div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
div[data-testid="stSelectbox"] div[data-baseweb="select"] input,
div[data-testid="stSelectbox"] div[data-baseweb="select"] p {
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    opacity: 1 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    line-height: 1.35 !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] input {
    caret-color: var(--crimson-2) !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div > div {
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {
    fill: var(--maroon-800) !important;
    transition: transform 0.28s var(--ease-smooth) !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div[aria-expanded="true"] svg {
    transform: rotate(180deg);
}

/* Disabled state — still readable, not invisible */
div[data-testid="stSelectbox"] div[data-baseweb="select"][aria-disabled="true"] > div,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div[disabled] {
    background: var(--paper-2) !important;
    opacity: 1 !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"][aria-disabled="true"] span,
div[data-testid="stSelectbox"] div[data-baseweb="select"][aria-disabled="true"] div,
div[data-testid="stSelectbox"] div[data-baseweb="select"][aria-disabled="true"] p {
    color: var(--ink-soft) !important;
    -webkit-text-fill-color: var(--ink-soft) !important;
}

/* Popover — anchored below trigger, no transform (transform breaks BaseWeb placement) */
div[data-baseweb="popover"] {
    z-index: 999999 !important;
    border-radius: 12px !important;
    border: 1px solid var(--line) !important;
    box-shadow: 0 12px 36px -10px rgba(43,7,7,0.28) !important;
    animation: fadeIn 0.15s var(--ease-smooth) both !important;
}
div[data-baseweb="popover"] ul[role="listbox"] {
    max-height: min(320px, 50vh) !important;
    overflow-y: auto !important;
    -webkit-overflow-scrolling: touch;
}
div[data-baseweb="popover"] li {
    color: var(--ink) !important;
    background: var(--white) !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    transition: background-color 0.18s var(--ease-smooth), color 0.18s var(--ease-smooth) !important;
}
div[data-baseweb="popover"] li:hover,
div[data-baseweb="popover"] li[aria-selected="true"] {
    background: #FCEEEE !important;
}
div[data-baseweb="popover"] li span,
div[data-baseweb="popover"] li div,
div[data-baseweb="popover"] li p {
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
}
div[data-baseweb="popover"] li:hover span,
div[data-baseweb="popover"] li:hover div,
div[data-baseweb="popover"] li[aria-selected="true"] span,
div[data-baseweb="popover"] li[aria-selected="true"] div {
    color: var(--crimson-2) !important;
    -webkit-text-fill-color: var(--crimson-2) !important;
}

/* ── Search button ── */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(150deg, var(--crimson-2), var(--maroon-800)) !important;
    color: #FFF5EE !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.04em !important;
    height: 46px !important;
    width: 100% !important;
    transition:
        transform 0.28s var(--ease-smooth),
        box-shadow 0.28s var(--ease-smooth),
        filter 0.28s var(--ease-smooth) !important;
    box-shadow: 0 8px 20px -8px rgba(142,18,18,0.55) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    filter: brightness(1.05) !important;
    box-shadow: 0 14px 28px -8px rgba(142,18,18,0.62) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:active {
    transform: translateY(0) scale(0.98) !important;
    transition-duration: 0.12s !important;
}

/* ── Selection summary ── */
.selection-track {
    display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;
    margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--paper-2);
    animation: fadeIn 0.35s var(--ease-smooth) both;
}
.sel-chip {
    display: inline-flex; align-items: center; gap: 0.35rem;
    padding: 0.4rem 0.85rem; border-radius: 999px;
    font-size: 0.8rem; font-weight: 600;
    background: var(--paper-2); border: 1px solid var(--line); color: var(--ink-soft);
    transition:
        background-color 0.3s var(--ease-smooth),
        border-color 0.3s var(--ease-smooth),
        color 0.3s var(--ease-smooth),
        transform 0.3s var(--ease-spring),
        box-shadow 0.3s var(--ease-smooth);
    max-width: 100%; word-break: break-word;
}
.sel-chip.active {
    background: #FFF0F0; border-color: #E8A8A8;
    color: var(--ink) !important;
    box-shadow: 0 2px 8px -2px rgba(168,22,27,0.18);
    animation: chipIn 0.35s var(--ease-spring) both;
}
.sel-chip.active .sel-val {
    color: var(--crimson-2) !important;
    font-weight: 700;
}
.sel-chip .sel-lab {
    font-size: 0.62rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ink-faint); font-weight: 700;
}
.sel-chip.active .sel-lab { color: var(--crimson-2); opacity: 0.75; }
.sel-arrow {
    color: var(--ink-faint); font-size: 0.8rem;
    transition: transform 0.3s var(--ease-smooth), opacity 0.3s ease;
}

/* ── Results ── */
.status-banner {
    display: flex; align-items: flex-start; gap: 0.5rem;
    background: #FFF4F4; border: 1px solid #F0C7C7; color: var(--crimson-2);
    border-radius: 12px; padding: 0.85rem 1rem; font-size: 0.85rem;
    margin-bottom: 1.25rem;
}
.results-bar {
    display: flex; align-items: center; justify-content: space-between;
    gap: 0.75rem; flex-wrap: wrap; margin: 0.5rem 0 1rem 0;
}
.results-title {
    font-family: 'Fraunces', serif; font-size: clamp(1.05rem, 3vw, 1.2rem);
    font-weight: 600; color: var(--maroon-900);
}
.results-title .who { color: var(--crimson-2); }
.results-pill {
    font-size: 0.7rem; font-weight: 700;
    color: #FFF5EE; background: var(--crimson-2);
    padding: 0.3rem 0.75rem; border-radius: 999px; white-space: nowrap;
}

.card {
    background: var(--white); border-radius: 16px; border: 1px solid var(--line);
    padding: 1.25rem 1.5rem; margin-bottom: 0.85rem;
    box-shadow: 0 8px 24px -18px rgba(43,7,7,0.3);
    transition:
        transform 0.32s var(--ease-smooth),
        box-shadow 0.32s var(--ease-smooth),
        border-color 0.32s var(--ease-smooth);
    animation: fadeUp 0.45s var(--ease-smooth) both;
}
.card:nth-of-type(1) { animation-delay: 0.04s; }
.card:nth-of-type(2) { animation-delay: 0.1s; }
.card:nth-of-type(3) { animation-delay: 0.16s; }
.card:nth-of-type(4) { animation-delay: 0.22s; }
.card:nth-of-type(n+5) { animation-delay: 0.28s; }
.card:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 36px -14px rgba(43,7,7,0.38);
    border-color: #E8D5D5;
}
.card::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
    border-radius: 16px 0 0 16px;
}
.card { position: relative; overflow: hidden; }
.card.type-theory::before    { background: var(--crimson-2); }
.card.type-tutorial::before  { background: #C9842E; }
.card.type-lab::before       { background: #2E5DC9; }
.card.type-practical::before { background: #2E9956; }
.card.type-extra::before     { background: #7A4FC9; }

.card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; gap: 0.5rem; flex-wrap: wrap; }
.chip {
    font-size: 0.62rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase;
    padding: 0.28rem 0.65rem; border-radius: 999px;
}
.chip-theory    { background: #FCEEEE; color: var(--crimson-2); }
.chip-tutorial  { background: #FBF1E2; color: #8E5C12; }
.chip-lab       { background: #EAF0FD; color: #1C3FA8; }
.chip-practical { background: #E9F8EE; color: #1C7740; }
.chip-extra     { background: #F2ECFB; color: #5A35A8; }
.card-index { font-size: 0.65rem; color: var(--ink-faint); }
.card-subject {
    font-family: 'Fraunces', serif;
    font-size: clamp(1rem, 3vw, 1.15rem); font-weight: 600;
    color: var(--ink); line-height: 1.35; margin-bottom: 1rem;
}
.card-meta {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 0.85rem 1.25rem;
    padding-top: 0.85rem; border-top: 1px dashed var(--paper-2);
}
.meta-label {
    font-size: 0.6rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--ink-faint); margin-bottom: 0.2rem;
}
.meta-value { font-size: 0.9rem; font-weight: 600; color: var(--ink); word-break: break-word; }

.empty-box {
    background: var(--white); border: 1.5px dashed var(--line);
    border-radius: 16px; padding: clamp(2rem, 6vw, 3rem) 1.25rem;
    text-align: center; margin-top: 0.5rem;
}
.empty-title {
    font-family: 'Fraunces', serif; font-size: 1.1rem; font-weight: 600;
    color: var(--maroon-900); margin-bottom: 0.4rem;
}
.empty-sub { font-size: 0.85rem; color: var(--ink-soft); line-height: 1.6; max-width: 420px; margin: 0 auto; }

.soft-divider { height: 1px; background: var(--line); margin: 2rem 0 1.25rem 0; }
.footer { text-align: center; padding-bottom: 1rem; }
.footer-line1 { font-size: 0.78rem; font-weight: 600; color: var(--maroon-900); }
.footer-line2 { font-size: 0.7rem; color: var(--ink-faint); margin-top: 0.3rem; line-height: 1.5; }

div[data-testid="stAlert"] { border-radius: 12px !important; }

/* ── Responsive: stack form fields on small screens ── */
@media (max-width: 768px) {
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    .hero { margin-left: -1rem; margin-right: -1rem; }
    .hero-stats { width: 100%; justify-content: space-around; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.panel-head) {
        padding: 1.15rem 1rem 1rem 1rem !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) {
        flex-direction: column !important;
        gap: 0.15rem !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) > div[data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    .selection-track { gap: 0.35rem; }
    .sel-arrow { display: none; }
    .sel-chip { font-size: 0.74rem; }
}

@media (max-width: 480px) {
    .hero-brand { flex-direction: column; align-items: flex-start; }
    .panel-head { flex-direction: column; align-items: flex-start; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
""", unsafe_allow_html=True)

st.components.v1.html("""
<script>
(function () {
  try {
    var doc = window.parent.document;
  } catch (e) {
    return; // cross-origin iframe — nothing below is safe to run
  }
  const PLACEHOLDERS = ["Select professor", "Select day", "Select time"];
  const INK = "#1A1110";
  const INK_SOFT = "#5A4642";
  let patchTimer = 0;

  // This only patches text color for legibility — it never touches
  // position/transform, so the popover's own native placement (which
  // anchors it correctly under the field) is always left alone.
  function patchSelectText() {
    doc.querySelectorAll('[data-testid="stSelectbox"] [data-baseweb="select"]').forEach(function (el) {
      const text = (el.textContent || "").trim();
      const isPlaceholder = PLACEHOLDERS.indexOf(text) !== -1;
      const isDisabled = el.getAttribute("aria-disabled") === "true";
      el.classList.toggle("is-selected", !isPlaceholder && !isDisabled);

      el.querySelectorAll("div, span, p, input").forEach(function (node) {
        if (node.closest('[data-baseweb="popover"]')) return;
        const color = isDisabled ? INK_SOFT : INK;
        node.style.setProperty("color", color, "important");
        node.style.setProperty("-webkit-text-fill-color", color, "important");
        node.style.setProperty("opacity", "1", "important");
      });
    });
  }

  function schedulePatch() {
    clearTimeout(patchTimer);
    patchTimer = setTimeout(patchSelectText, 80);
  }

  patchSelectText();

  new MutationObserver(function (mutations) {
    for (var i = 0; i < mutations.length; i++) {
      var m = mutations[i];
      if (m.type === "attributes" && m.attributeName === "aria-expanded") {
        schedulePatch();
        break;
      }
    }
  }).observe(doc.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["aria-expanded", "aria-disabled"],
  });
})();
</script>
""", height=0)


# ════════════════════════════════════════════════════════════════════════════
# HERO
# ════════════════════════════════════════════════════════════════════════════
n_profs = len(all_professors)
n_records = len(df)
n_divisions = df["division"].nunique() if DATA_OK else 0

st.markdown(f"""
<div class="hero">
  <div class="hero-inner">
    <div class="hero-brand">
      <div class="hero-crest">🎓</div>
      <div>
        <div class="hero-eyebrow">Marathwada Mitra Mandal's College of Engineering, Pune</div>
        <div class="hero-title">MMCOE <em>Teacher</em> Assistant</div>
        <div class="hero-sub">Find your lecture instantly — select your name, day, and time slot from the live timetable.</div>
      </div>
    </div>
    <div class="hero-stats">
      <div class="hero-stat"><div class="num">{n_profs}</div><div class="lbl">Faculty</div></div>
      <div class="hero-stat"><div class="num">{n_divisions}</div><div class="lbl">Divisions</div></div>
      <div class="hero-stat"><div class="num">{n_records}</div><div class="lbl">Sessions</div></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# DATA-MISSING GUARD
# ════════════════════════════════════════════════════════════════════════════
if not DATA_OK:
    st.markdown("""
    <div class="status-banner">
      ⚠️ <span><b>timetable_data.csv</b> could not be loaded or is empty. Place the CSV next to <b>app.py</b> and restart.</span>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ════════════════════════════════════════════════════════════════════════════
# SESSION STATE — safe defaults
# ════════════════════════════════════════════════════════════════════════════
for key, default in (
    ("prof_select", PLACEHOLDER_PROF),
    ("day_select", PLACEHOLDER_DAY),
    ("time_select", PLACEHOLDER_TIME),
):
    if key not in st.session_state:
        st.session_state[key] = default


# ════════════════════════════════════════════════════════════════════════════
# SEARCH PANEL — cascading options derived from CSV per selection step
# ════════════════════════════════════════════════════════════════════════════
prof_options = [PLACEHOLDER_PROF] + all_professors
_ensure_option("prof_select", prof_options, PLACEHOLDER_PROF)
selected_prof = st.session_state["prof_select"]

day_options = [PLACEHOLDER_DAY] + _days_for_professor(selected_prof)
_ensure_option("day_select", day_options, PLACEHOLDER_DAY)
selected_day = st.session_state["day_select"]

time_options = [PLACEHOLDER_TIME] + _times_for_professor_day(selected_prof, selected_day)
_ensure_option("time_select", time_options, PLACEHOLDER_TIME)
selected_time = st.session_state["time_select"]

with st.container(border=True):
    st.markdown("""
    <div class="panel-head">
      <div class="panel-title">Find a lecture</div>
      <div class="panel-kicker">Faculty → Day → Time</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([2.2, 1.4, 2.2, 1.2], gap="small")

    with col1:
        prof_filled = " filled" if selected_prof != PLACEHOLDER_PROF else ""
        st.markdown(f'<div class="field-label{prof_filled}">Faculty name</div>', unsafe_allow_html=True)
        selected_prof = st.selectbox(
            "Faculty name",
            options=prof_options,
            label_visibility="collapsed",
            key="prof_select",
            on_change=_on_professor_change,
        )

    with col2:
        day_muted = "" if selected_prof != PLACEHOLDER_PROF else " muted"
        day_filled = " filled" if selected_day != PLACEHOLDER_DAY else ""
        st.markdown(f'<div class="field-label{day_muted}{day_filled}">Day</div>', unsafe_allow_html=True)
        selected_day = st.selectbox(
            "Day",
            options=day_options,
            label_visibility="collapsed",
            key="day_select",
            on_change=_on_day_change,
            disabled=selected_prof == PLACEHOLDER_PROF,
        )

    with col3:
        time_muted = "" if selected_day != PLACEHOLDER_DAY else " muted"
        time_filled = " filled" if selected_time != PLACEHOLDER_TIME else ""
        st.markdown(f'<div class="field-label{time_muted}{time_filled}">Time slot</div>', unsafe_allow_html=True)
        selected_time = st.selectbox(
            "Time slot",
            options=time_options,
            label_visibility="collapsed",
            key="time_select",
            disabled=selected_day == PLACEHOLDER_DAY,
        )
        if selected_prof != PLACEHOLDER_PROF and selected_day != PLACEHOLDER_DAY:
            n_slots = len(time_options) - 1
            st.markdown(
                f'<div class="field-hint">{n_slots} slot{"s" if n_slots != 1 else ""} for this day</div>',
                unsafe_allow_html=True,
            )

    with col4:
        st.markdown('<div class="field-label">&nbsp;</div>', unsafe_allow_html=True)
        search_clicked = st.button("Search", use_container_width=True, type="primary")

    prof_active = selected_prof != PLACEHOLDER_PROF
    day_active = selected_day != PLACEHOLDER_DAY
    time_active = selected_time != PLACEHOLDER_TIME

    prof_disp = escape_html(selected_prof) if prof_active else "—"
    day_disp = escape_html(selected_day) if day_active else "—"
    time_disp = escape_html(selected_time) if time_active else "—"

    st.markdown(f"""
    <div class="selection-track">
      <span class="sel-chip {'active' if prof_active else ''}">
        <span>👤</span>
        <span class="sel-lab">Faculty</span>
        <span class="sel-val">{prof_disp}</span>
      </span>
      <span class="sel-arrow">→</span>
      <span class="sel-chip {'active' if day_active else ''}">
        <span>📅</span>
        <span class="sel-lab">Day</span>
        <span class="sel-val">{day_disp}</span>
      </span>
      <span class="sel-arrow">→</span>
      <span class="sel-chip {'active' if time_active else ''}">
        <span>🕐</span>
        <span class="sel-lab">Time</span>
        <span class="sel-val">{time_disp}</span>
      </span>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# RESULTS
# ════════════════════════════════════════════════════════════════════════════
TYPE_CHIP_MAP = {
    "theory":    ("chip-theory",    "type-theory",    "Theory"),
    "tutorial":  ("chip-tutorial",  "type-tutorial",  "Tutorial"),
    "lab":       ("chip-lab",       "type-lab",       "Lab"),
    "practical": ("chip-practical", "type-practical", "Practical"),
}


def classify(ltype: str):
    t = (ltype or "").lower()
    if "theory" in t:
        return TYPE_CHIP_MAP["theory"]
    if "tutorial" in t:
        return TYPE_CHIP_MAP["tutorial"]
    if "lab" in t:
        return TYPE_CHIP_MAP["lab"]
    if "practical" in t:
        return TYPE_CHIP_MAP["practical"]
    return ("chip-extra", "type-extra", ltype.title() if ltype else "Session")


if search_clicked:
    if not (prof_active and day_active and time_active):
        st.warning("Please select faculty, day, and time slot before searching.")
    else:
        results = df[
            (df["professor"] == selected_prof)
            & (df["day"] == selected_day)
            & (df["time_slot"] == selected_time)
        ].copy()

        if results.empty:
            st.markdown(f"""
            <div class="empty-box">
              <div class="empty-title">No scheduled session</div>
              <div class="empty-sub">
                <b>{escape_html(selected_prof)}</b> has no class on
                <b>{escape_html(selected_day)}</b> at <b>{escape_html(selected_time)}</b>.
                This may be a free period.
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            n = len(results)
            st.markdown(f"""
            <div class="results-bar">
              <div class="results-title">Schedule for <span class="who">{escape_html(selected_prof)}</span></div>
              <div class="results-pill">{n} session{"s" if n != 1 else ""}</div>
            </div>
            """, unsafe_allow_html=True)

            total = len(results)
            for idx, (_, row) in enumerate(results.iterrows(), start=1):
                chip_cls, card_cls, chip_label = classify(row["type"])
                index_tag = f"{idx:02d} / {total:02d}" if total > 1 else ""
                st.markdown(f"""
                <div class="card {card_cls}">
                  <div class="card-top">
                    <span class="chip {chip_cls}">{chip_label}</span>
                    <span class="card-index">{index_tag}</span>
                  </div>
                  <div class="card-subject">{escape_html(row['subject'])}</div>
                  <div class="card-meta">
                    <div>
                      <div class="meta-label">Room</div>
                      <div class="meta-value">{escape_html(row['room'])}</div>
                    </div>
                    <div>
                      <div class="meta-label">Division</div>
                      <div class="meta-value">{escape_html(row['division'])}</div>
                    </div>
                    <div>
                      <div class="meta-label">Day</div>
                      <div class="meta-value">{escape_html(row['day'])}</div>
                    </div>
                    <div>
                      <div class="meta-label">Time</div>
                      <div class="meta-value">{escape_html(row['time_slot'])}</div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="footer">
  <div class="footer-line1">MMCOE Teacher Assistant — Engineering Science &amp; Humanities</div>
  <div class="footer-line2">Marathwada Mitra Mandal's College of Engineering, Pune · A.Y. 2025–26</div>
</div>
""", unsafe_allow_html=True)
