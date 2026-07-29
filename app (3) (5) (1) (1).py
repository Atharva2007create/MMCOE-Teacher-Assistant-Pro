import streamlit as st
import pandas as pd
import os
import re

# ═════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═════════════════════════════════════════════════════════════════
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


def _get_professor_schedule(prof: str) -> dict:
    """Returns schedule grouped by day for a professor"""
    if prof == PLACEHOLDER_PROF or prof not in all_professors:
        return {day: [] for day in DAY_ORDER}
    
    # Check if there are any assignments for this day
    prof_data = df[df["professor"] == prof].copy()
    
    # Also include assignments from the session state
    if "assignments" in st.session_state and st.session_state["assignments"]:
        for assignment in st.session_state["assignments"]:
            if assignment["professor"] == prof:
                # Add this assignment to the data
                prof_data = pd.concat([
                    prof_data,
                    pd.DataFrame([{
                        "professor": assignment["professor"],
                        "day": assignment["day"],
                        "time_slot": assignment["time_slot"],
                        "division": assignment["division"],
                        "subject": assignment["subject"],
                        "room": assignment["room"],
                        "type": assignment["type"]
                    }])
                ], ignore_index=True)
    
    schedule = {day: [] for day in DAY_ORDER}
    
    for day in DAY_ORDER:
        day_sessions = prof_data[prof_data["day"] == day]
        if not day_sessions.empty:
            day_sessions = day_sessions.sort_values("time_slot", key=lambda x: x.apply(_time_sort_key))
            schedule[day] = day_sessions.to_dict('records')
    
    return schedule


def classify(ltype: str):
    """Classify session type and return chip styling"""
    TYPE_CHIP_MAP = {
        "theory":    ("chip-theory",    "type-theory",    "Theory"),
        "tutorial":  ("chip-tutorial",  "type-tutorial",  "Tutorial"),
        "lab":       ("chip-lab",       "type-lab",       "Lab"),
        "practical": ("chip-practical", "type-practical", "Practical"),
    }
    
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


# ════════════════════════════════════════════════════════════════
# STYLES
# ════════════════════════════════════════════════════════════════
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

/* ── Day Section ── */
.day-section {
    margin-bottom: 1.75rem;
    animation: fadeIn 0.4s var(--ease-smooth) both;
}
.day-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 0;
    margin-bottom: 1rem;
    border-bottom: 2px solid var(--line);
}
.day-emoji {
    font-size: 1.5rem;
}
.day-title {
    font-family: 'Fraunces', serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--maroon-900);
    flex: 1;
}
.day-count {
    font-size: 0.72rem;
    color: var(--ink-faint);
    font-weight: 600;
    background: var(--paper-2);
    padding: 0.35rem 0.65rem;
    border-radius: 999px;
}

.no-schedule {
    background: var(--white);
    border: 1.5px dashed var(--line);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    color: var(--ink-faint);
    font-size: 0.9rem;
}

/* ── Brief Card (clickable) ── */
.brief-card {
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    cursor: pointer;
    transition:
        transform 0.28s var(--ease-smooth),
        box-shadow 0.28s var(--ease-smooth),
        border-color 0.28s var(--ease-smooth);
    animation: fadeUp 0.35s var(--ease-smooth) both;
    position: relative;
    overflow: hidden;
}
.brief-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px -8px rgba(43,7,7,0.3);
    border-color: #E8D5D5;
}
.brief-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    border-radius: 12px 0 0 12px;
}
.brief-card.type-theory::before    { background: var(--crimson-2); }
.brief-card.type-tutorial::before  { background: #C9842E; }
.brief-card.type-lab::before       { background: #2E5DC9; }
.brief-card.type-practical::before { background: #2E9956; }
.brief-card.type-extra::before     { background: #7A4FC9; }

.brief-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.65rem;
    gap: 0.5rem;
    flex-wrap: wrap;
}
.brief-chip {
    font-size: 0.6rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
}
.brief-chip.chip-theory    { background: #FCEEEE; color: var(--crimson-2); }
.brief-chip.chip-tutorial  { background: #FBF1E2; color: #8E5C12; }
.brief-chip.chip-lab       { background: #EAF0FD; color: #1C3FA8; }
.brief-chip.chip-practical { background: #E9F8EE; color: #1C7740; }
.brief-chip.chip-extra     { background: #F2ECFB; color: #5A35A8; }

.brief-subject {
    font-family: 'Fraunces', serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--ink);
    line-height: 1.3;
    margin-bottom: 0.5rem;
}
.brief-meta {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    font-size: 0.8rem;
    color: var(--ink-soft);
}
.brief-meta-item {
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

/* ── Detailed Card (modal-like) ── */
.detailed-card {
    background: var(--white);
    border-radius: 16px;
    border: 1px solid var(--line);
    padding: 1.75rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 12px 32px -12px rgba(43,7,7,0.35);
    animation: fadeUp 0.45s var(--ease-smooth) both;
    position: relative;
    overflow: hidden;
}
.detailed-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 5px;
}
.detailed-card.type-theory::before    { background: var(--crimson-2); }
.detailed-card.type-tutorial::before  { background: #C9842E; }
.detailed-card.type-lab::before       { background: #2E5DC9; }
.detailed-card.type-practical::before { background: #2E9956; }
.detailed-card.type-extra::before     { background: #7A4FC9; }

.detailed-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    gap: 0.75rem;
    flex-wrap: wrap;
}
.detailed-chip {
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
}
.detailed-chip.chip-theory    { background: #FCEEEE; color: var(--crimson-2); }
.detailed-chip.chip-tutorial  { background: #FBF1E2; color: #8E5C12; }
.detailed-chip.chip-lab       { background: #EAF0FD; color: #1C3FA8; }
.detailed-chip.chip-practical { background: #E9F8EE; color: #1C7740; }
.detailed-chip.chip-extra     { background: #F2ECFB; color: #5A35A8; }

.detailed-close {
    background: var(--paper-2);
    border: none;
    color: var(--ink-soft);
    cursor: pointer;
    font-size: 1.4rem;
    padding: 0;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s var(--ease-smooth);
}
.detailed-close:hover {
    background: var(--line);
    color: var(--ink);
}

.detailed-subject {
    font-family: 'Fraunces', serif;
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--ink);
    line-height: 1.4;
    margin-bottom: 1.25rem;
}

.detailed-meta {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1.25rem 1.75rem;
    padding-top: 1.25rem;
    border-top: 1px dashed var(--paper-2);
}
.meta-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--ink-faint);
    margin-bottom: 0.35rem;
}
.meta-value {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--ink);
    word-break: break-word;
}

/* ── Assignment Section ── */
.assignment-section {
    margin-top: 1.75rem;
    padding-top: 1.5rem;
    border-top: 2px solid var(--paper-2);
    animation: fadeIn 0.5s var(--ease-smooth) both;
}
.assignment-title {
    font-family: 'Fraunces', serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--maroon-900);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.assignment-content {
    background: #FFFBFB;
    border: 1px solid #F0C7C7;
    border-radius: 12px;
    padding: 1.25rem;
}
.assignment-control {
    display: flex;
    align-items: flex-end;
    gap: 0.75rem;
    flex-wrap: wrap;
}
.assignment-dropdown {
    flex: 1;
    min-width: 200px;
}
.assignment-button {
    padding: 0.65rem 1.25rem;
    background: linear-gradient(150deg, var(--crimson-2), var(--maroon-800));
    color: #FFF5EE;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    letter-spacing: 0.04em;
    cursor: pointer;
    transition: all 0.2s var(--ease-smooth);
}
.assignment-button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(168, 22, 27, 0.3);
}
.assignment-button:active {
    transform: translateY(0) scale(0.98);
}

.assignment-confirmation {
    background: #E9F8EE;
    border: 1px solid #C7E8D8;
    border-radius: 8px;
    padding: 1rem;
    margin-top: 1rem;
    color: #1C7740;
    font-size: 0.9rem;
    animation: fadeIn 0.3s var(--ease-smooth) both;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}

.remove-button {
    padding: 0.5rem 1rem;
    background: #E8A8A8;
    color: #8B0000;
    border: 1px solid #D4A8A8;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s var(--ease-smooth);
    white-space: nowrap;
}
.remove-button:hover {
    background: #D99090;
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(168, 22, 27, 0.2);
}
.remove-button:active {
    transform: translateY(0) scale(0.98);
}

.back-button {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--crimson-2);
    cursor: pointer;
    margin-bottom: 1rem;
    transition: color 0.2s var(--ease-smooth);
}
.back-button:hover {
    color: var(--maroon-900);
}

.empty-box {
    background: var(--white);
    border: 1.5px dashed var(--line);
    border-radius: 16px;
    padding: clamp(2rem, 6vw, 3rem) 1.25rem;
    text-align: center;
    margin-top: 0.5rem;
}
.empty-title {
    font-family: 'Fraunces', serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--maroon-900);
    margin-bottom: 0.4rem;
}
.empty-sub {
    font-size: 0.85rem;
    color: var(--ink-soft);
    line-height: 1.6;
    max-width: 420px;
    margin: 0 auto;
}

.soft-divider {
    height: 1px;
    background: var(--line);
    margin: 2rem 0 1.25rem 0;
}
.footer {
    text-align: center;
    padding-bottom: 1rem;
}
.footer-line1 {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--maroon-900);
}
.footer-line2 {
    font-size: 0.7rem;
    color: var(--ink-faint);
    margin-top: 0.3rem;
    line-height: 1.5;
}

div[data-testid="stAlert"] { border-radius: 12px !important; }

/* ── Responsive: stack form fields on small screens ── */
@media (max-width: 768px) {
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    .hero { margin-left: -1rem; margin-right: -1rem; }
    .hero-stats { width: 100%; justify-content: space-around; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.panel-head) {
        padding: 1.15rem 1rem 1rem 1rem !important;
    }
}

@media (max-width: 480px) {
    .hero-brand { flex-direction: column; align-items: flex-start; }
    .panel-head { flex-direction: column; align-items: flex-start; }
    .brief-meta { flex-direction: column; gap: 0.5rem; }
    .assignment-control { flex-direction: column; }
    .assignment-dropdown { min-width: 100%; }
    .assignment-confirmation { flex-direction: column; }
    .remove-button { width: 100%; }
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
    return;
  }
  const PLACEHOLDERS = ["Select professor"];
  const INK = "#1A1110";
  const INK_SOFT = "#5A4642";
  let patchTimer = 0;

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


# ════════════════════════════════════════════════════════════════
# HERO
# ════════════════════════════════════════════════════════════════
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
        <div class="hero-sub">Select your name to view your weekly timetable at a glance.</div>
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


# ════════════════════════════════════════════════════════════════
# DATA-MISSING GUARD
# ════════════════════════════════════════════════════════════════
if not DATA_OK:
    st.markdown("""
    <div class="status-banner">
      ⚠️ <span><b>timetable_data.csv</b> could not be loaded or is empty. Place the CSV next to <b>app.py</b> and restart.</span>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ════════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════════
if "prof_select" not in st.session_state:
    st.session_state["prof_select"] = PLACEHOLDER_PROF
if "selected_session_index" not in st.session_state:
    st.session_state["selected_session_index"] = None
if "assignments" not in st.session_state:
    st.session_state["assignments"] = []


# ════════════════════════════════════════════════════════════════
# PROFESSOR SELECTION PANEL
# ════════════════════════════════════════════════════════════════
prof_options = [PLACEHOLDER_PROF] + all_professors
selected_prof = st.session_state["prof_select"]

with st.container(border=True):
    st.markdown("""
    <div class="panel-head">
      <div class="panel-title">Select Faculty</div>
    </div>
    """, unsafe_allow_html=True)

    col1, _ = st.columns([2, 3], gap="small")
    
    with col1:
        prof_filled = " filled" if selected_prof != PLACEHOLDER_PROF else ""
        st.markdown(f'<div class="field-label{prof_filled}">Faculty name</div>', unsafe_allow_html=True)
        selected_prof = st.selectbox(
            "Faculty name",
            options=prof_options,
            label_visibility="collapsed",
            key="prof_select",
        )


# ════════════════════════════════════════════════════════════════
# TIMETABLE VIEW
# ════════════════════════════════════════════════════════════════

if selected_prof == PLACEHOLDER_PROF:
    st.markdown("""
    <div class="empty-box">
      <div class="empty-title">Welcome to your Timetable</div>
      <div class="empty-sub">
        Select your name from above to view your complete weekly schedule.
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Get professor's schedule
    schedule = _get_professor_schedule(selected_prof)
    
    # Display professor info header
    st.markdown(f"""
    <div style="margin: 1.5rem 0; padding: 1rem; background: #FFFBFB; border-left: 4px solid var(--crimson-2); border-radius: 8px;">
      <div style="font-family: 'Fraunces', serif; font-size: 1.15rem; font-weight: 600; color: var(--maroon-900);">
        📅 Weekly Timetable for <span style="color: var(--crimson-2);">{escape_html(selected_prof)}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Handle detailed view
    if st.session_state["selected_session_index"] is not None:
        session_key = st.session_state["selected_session_index"]
        
        # Parse the key to get day and index
        day, idx = session_key.split("_")
        idx = int(idx)
        
        if day in schedule and idx < len(schedule[day]):
            session = schedule[day][idx]
            
            # Back button
            if st.button("← Back to Schedule"):
                st.session_state["selected_session_index"] = None
                st.rerun()
            
            # Detailed card
            chip_cls, card_cls, chip_label = classify(session["type"])
            st.markdown(f"""
            <div class="detailed-card {card_cls}">
              <div class="detailed-top">
                <span class="detailed-chip {chip_cls}">{chip_label}</span>
              </div>
              <div class="detailed-subject">{escape_html(session['subject'])}</div>
              <div class="detailed-meta">
                <div>
                  <div class="meta-label">Faculty</div>
                  <div class="meta-value">{escape_html(session['professor'])}</div>
                </div>
                <div>
                  <div class="meta-label">Room</div>
                  <div class="meta-value">{escape_html(session['room'])}</div>
                </div>
                <div>
                  <div class="meta-label">Division</div>
                  <div class="meta-value">{escape_html(session['division'])}</div>
                </div>
                <div>
                  <div class="meta-label">Day</div>
                  <div class="meta-value">{escape_html(session['day'])}</div>
                </div>
                <div>
                  <div class="meta-label">Time</div>
                  <div class="meta-value">{escape_html(session['time_slot'])}</div>
                </div>
                <div>
                  <div class="meta-label">Type</div>
                  <div class="meta-value">{chip_label}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            
            # ════════════════════════════════════════════════════════════════
            # ASSIGNMENT SECTION
            # ════════════════════════════════════════════════════════════════
            
            # Check if already assigned
            existing_assignment = None
            for assignment in st.session_state["assignments"]:
                if (assignment["day"] == day and 
                    assignment["time_slot"] == session["time_slot"] and 
                    assignment["division"] == session["division"] and
                    assignment["subject"] == session["subject"]):
                    existing_assignment = assignment
                    break
            
            st.markdown("""
            <div class="assignment-section">
              <div class="assignment-title">
                👨‍🏫 Assign Another Professor for This Lecture
              </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.container():
                col1, col2 = st.columns([2, 1], gap="small")
                
                with col1:
                    st.markdown('<div class="field-label">Select Professor</div>', unsafe_allow_html=True)
                    assigned_prof = st.selectbox(
                        "Assign professor",
                        options=all_professors,
                        label_visibility="collapsed",
                        key=f"assign_prof_{session_key}",
                        index=None,
                        placeholder="Choose a professor..."
                    )
                
                with col2:
                    st.markdown('<div class="field-label">&nbsp;</div>', unsafe_allow_html=True)
                    if st.button("Assign", key=f"assign_btn_{session_key}", use_container_width=True):
                        if assigned_prof:
                            # Check if this exact assignment already exists
                            assignment_exists = False
                            for i, assignment in enumerate(st.session_state["assignments"]):
                                if (assignment["day"] == day and 
                                    assignment["time_slot"] == session["time_slot"] and 
                                    assignment["division"] == session["division"] and
                                    assignment["subject"] == session["subject"]):
                                    # Update existing
                                    st.session_state["assignments"][i]["professor"] = assigned_prof
                                    assignment_exists = True
                                    break
                            
                            if not assignment_exists:
                                # Add new assignment
                                st.session_state["assignments"].append({
                                    "professor": assigned_prof,
                                    "day": day,
                                    "time_slot": session["time_slot"],
                                    "division": session["division"],
                                    "subject": session["subject"],
                                    "room": session["room"],
                                    "type": session["type"]
                                })
                            
                            st.success(f"✅ {escape_html(assigned_prof)} has been assigned to this lecture for {escape_html(day)}!")
                            st.rerun()
            
            # Show current assignment status with remove button
            if existing_assignment:
                st.markdown(f"""
                <div class="assignment-confirmation">
                  <div>✓ Currently assigned: <strong>{escape_html(existing_assignment['professor'])}</strong> on <strong>{escape_html(day)}</strong></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Remove assignment button
                if st.button("🗑️ Remove Assignment", key=f"remove_btn_{session_key}", help="Remove the assigned professor from this lecture"):
                    # Find and remove the assignment
                    for i, assignment in enumerate(st.session_state["assignments"]):
                        if (assignment["day"] == day and 
                            assignment["time_slot"] == session["time_slot"] and 
                            assignment["division"] == session["division"] and
                            assignment["subject"] == session["subject"]):
                            st.session_state["assignments"].pop(i)
                            break
                    
                    st.warning(f"❌ Assignment removed! This lecture is no longer assigned to {escape_html(existing_assignment['professor'])}.")
                    st.rerun()
    
    else:
        # Display all days
        day_emojis = {
            "Monday": "🌅",
            "Tuesday": "☀️",
            "Wednesday": "🌤️",
            "Thursday": "⛅",
            "Friday": "🌆"
        }
        
        for day in DAY_ORDER:
            sessions = schedule[day]
            emoji = day_emojis.get(day, "📅")
            
            st.markdown(f"""
            <div class="day-section">
              <div class="day-header">
                <span class="day-emoji">{emoji}</span>
                <span class="day-title">{day}</span>
                <span class="day-count">{len(sessions)} session{"s" if len(sessions) != 1 else ""}</span>
              </div>
            """, unsafe_allow_html=True)
            
            if not sessions:
                st.markdown(f"""
                <div class="no-schedule">
                  No schedule on {day}
                </div>
                """, unsafe_allow_html=True)
            else:
                for idx, session in enumerate(sessions):
                    chip_cls, card_cls, chip_label = classify(session["type"])
                    session_key = f"{day}_{idx}"
                    
                    st.markdown(f"""
                    <div class="brief-card {card_cls}" onclick="window.parent.document.querySelector('[data-session-key=\"{session_key}\"]')?.click()">
                      <div class="brief-top">
                        <span class="brief-chip {chip_cls}">{chip_label}</span>
                      </div>
                      <div class="brief-subject">{escape_html(session['subject'])}</div>
                      <div class="brief-meta">
                        <div class="brief-meta-item">🕐 {escape_html(session['time_slot'])}</div>
                        <div class="brief-meta-item">📍 {escape_html(session['room'])}</div>
                        <div class="brief-meta-item">👥 {escape_html(session['division'])}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Hidden button to trigger session selection
                    if st.button("View Details", key=f"btn_{session_key}", help="Click to see full details"):
                        st.session_state["selected_session_index"] = session_key
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════
st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="footer">
  <div class="footer-line1">MMCOE Teacher Assistant — Engineering Science & Humanities</div>
  <div class="footer-line2">Marathwada Mitra Mandal's College of Engineering, Pune · A.Y. 2025–26</div>
</div>
""", unsafe_allow_html=True)
