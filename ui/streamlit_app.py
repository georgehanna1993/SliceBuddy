import json
import time
import requests
import streamlit as st

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="SliceBuddy",
    page_icon="🟩",
    layout="wide",
)

API_URL = "http://127.0.0.1:8000/plan"  # backend endpoint (NOT shown in UI)

# =========================
# THEME COLORS (tweak if you want)
# These are close to your reference image.
# =========================
GREEN = "#16a34a"        # primary green
GREEN_DARK = "#0f7a35"   # darker green for hover
BG = "#f6f7f9"           # app background
CARD = "#ffffff"         # card background
TEXT = "#0f172a"         # main text
MUTED = "#64748b"        # muted text
BORDER = "#e5e7eb"       # borders
SIDEBAR_BG = "#ffffff"   # sidebar bg

# =========================
# CSS (makes Streamlit look like your reference UI)
# =========================
st.markdown(
    f"""
<style>
/* App background */
.stApp {{
    background: {BG};
}}

/* Kill Streamlit default top padding */
.block-container {{
    padding-top: 1.0rem !important;
    padding-bottom: 6rem !important; /* space for sticky input */
}}

/* Sidebar styling */
section[data-testid="stSidebar"] {{
    background: {SIDEBAR_BG};
    border-right: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] .block-container {{
    padding-top: 1rem;
}}

/* Hide Streamlit footer/menu */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

/* Top header bar (green) */
.sb-topbar {{
    background: {GREEN};
    color: white;
    border-radius: 14px;
    padding: 14px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
}}
.sb-topbar .left {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.sb-logo {{
    width: 38px;
    height: 38px;
    border-radius: 12px;
    background: rgba(255,255,255,0.18);
    display: grid;
    place-items: center;
    font-weight: 800;
}}
.sb-title {{
    font-size: 18px;
    font-weight: 800;
    line-height: 1.1;
}}
.sb-sub {{
    font-size: 12px;
    opacity: 0.9;
}}
.sb-badge {{
    font-size: 12px;
    background: rgba(255,255,255,0.20);
    padding: 6px 10px;
    border-radius: 999px;
    font-weight: 700;
}}
.sb-actions {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.sb-iconbtn {{
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: rgba(255,255,255,0.18);
    display: grid;
    place-items: center;
    cursor: pointer;
    user-select: none;
}}
.sb-iconbtn:hover {{
    background: rgba(255,255,255,0.25);
}}

/* Chat area look */
.sb-chat-wrap {{
    max-width: 980px;
    margin: 0 auto;
}}

/* User bubble */
.sb-user {{
    display: flex;
    justify-content: flex-end;
    margin: 16px 0;
}}
.sb-user .bubble {{
    background: {GREEN};
    color: white;
    padding: 14px 16px;
    border-radius: 16px;
    max-width: 75%;
    font-weight: 600;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
}}

/* Assistant message container (white card) */
.sb-assistant {{
    display: flex;
    gap: 14px;
    align-items: flex-start;
    margin: 18px 0;
}}
.sb-assistant .botbadge {{
    width: 42px;
    height: 42px;
    border-radius: 999px;
    background: rgba(22,163,74,0.12);
    display: grid;
    place-items: center;
    color: {GREEN};
    font-weight: 900;
    flex-shrink: 0;
}}
.sb-assistant .content {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 16px 18px;
    width: 100%;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
}}
.sb-h1 {{
    font-size: 18px;
    font-weight: 900;
    margin: 0 0 6px 0;
    color: {TEXT};
}}
.sb-p {{
    color: {TEXT};
    margin: 0 0 14px 0;
}}
.sb-section {{
    border-radius: 16px;
    border: 1px solid {BORDER};
    background: #fbfbfc;
    padding: 14px 14px;
    margin-top: 12px;
}}
.sb-section-title {{
    font-weight: 900;
    color: {TEXT};
    margin-bottom: 8px;
    display:flex;
    align-items:center;
    gap:10px;
}}
.sb-kv {{
    display:grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 8px;
}}
.sb-kv .item {{
    background: white;
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 12px;
}}
.sb-kv .label {{
    font-size: 12px;
    color: {MUTED};
    font-weight: 800;
    letter-spacing: 0.02em;
}}
.sb-kv .value {{
    margin-top: 6px;
    font-size: 14px;
    color: {TEXT};
    font-weight: 800;
}}
.sb-bullets {{
    margin: 0;
    padding-left: 18px;
    color: {TEXT};
}}
.sb-bullets li {{
    margin: 6px 0;
}}

/* Sticky bottom input bar (green) */
.sb-bottombar {{
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    background: {GREEN};
    padding: 14px 14px;
    z-index: 9999;
    border-top: 1px solid rgba(255,255,255,0.25);
}}
.sb-bottom-inner {{
    max-width: 980px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    gap: 12px;
}}
.sb-hint {{
    color: rgba(255,255,255,0.85);
    font-size: 12px;
    font-weight: 700;
}}
/* Make Streamlit chat input blend */
div[data-testid="stChatInput"] {{
    background: transparent !important;
}}
div[data-testid="stChatInput"] > div {{
    border-radius: 16px !important;
    border: none !important;
}}
div[data-testid="stChatInput"] textarea {{
    border-radius: 16px !important;
    border: none !important;
    padding: 12px 14px !important;
}}


</style>
""",
    unsafe_allow_html=True
)

st.markdown("""
<style>
/* ===== Sidebar: FORCE readable text (black) ===== */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] * {
  color: #0f172a !important; /* black-ish */
}

/* Sidebar headings and labels */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] label {
  color: #0f172a !important;
}

/* Sidebar buttons (text inside) */
section[data-testid="stSidebar"] button,
section[data-testid="stSidebar"] button * {
  color: #0f172a !important;
}

/* Sidebar "No plans yet." / captions */
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {
  color: #475569 !important;
}

/* Optional: make sidebar background explicitly white */
section[data-testid="stSidebar"] {
  background: #ffffff !important;
  border-right: 1px solid #e5e7eb !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# SESSION STATE
# =========================
if "plans" not in st.session_state:
    st.session_state.plans = []  # list of dicts: {title, ts, user_text, result}

if "active_idx" not in st.session_state:
    st.session_state.active_idx = None


# =========================
# Helpers
# =========================
def extract_title(user_text: str) -> str:
    t = user_text.strip().split("\n")[0][:40]
    return t if t else "New Print Plan"

def parse_dimensions_from_text(text: str):
    """
    Minimal parser: expects user to type: height 120 width 30
    If missing, we default to None and backend can handle assumptions.
    """
    import re
    def find_num(key):
        m = re.search(rf"{key}\s*[:=]?\s*(-?\d+(\.\d+)?)", text, re.IGNORECASE)
        return float(m.group(1)) if m else None

    h = find_num("height")
    w = find_num("width")
    return h, w

def call_backend(user_text: str):
    h, w = parse_dimensions_from_text(user_text)
    payload = {
        "description": user_text.strip(),
        "height_mm": h if h is not None else 0,
        "width_mm": w if w is not None else 0,
    }
    r = requests.post(API_URL, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()

def render_plan(result: dict):
    plan = result.get("plan", {})
    explanation = result.get("plan_explanation", "").strip()

    material = plan.get("material", {})
    orientation = plan.get("orientation", {})
    slicer = plan.get("slicer_settings", {}).get("settings", {})
    risks = plan.get("risks", {})

    st.markdown('<div class="sb-assistant">', unsafe_allow_html=True)
    st.markdown('<div class="botbadge">SB</div>', unsafe_allow_html=True)
    st.markdown('<div class="content">', unsafe_allow_html=True)

    st.markdown(f'<div class="sb-h1">Print Plan Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sb-p">{explanation.splitlines()[0] if explanation else "Here’s a structured print plan based on your description."}</div>',
        unsafe_allow_html=True
    )

    # Recommended Print Settings (grid)
    st.markdown('<div class="sb-section">', unsafe_allow_html=True)
    st.markdown('<div class="sb-section-title">🛠️ Recommended Print Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-kv">', unsafe_allow_html=True)

    def kv(label, value):
        st.markdown(
            f"""
            <div class="item">
              <div class="label">{label}</div>
              <div class="value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    kv("Layer Height", f"{slicer.get('layer_height_mm', '—')} mm")
    kv("Infill", f"{slicer.get('infill_percent', '—')}%")
    kv("Walls", f"{slicer.get('walls', '—')}")
    kv("Top/Bottom", f"{slicer.get('top_bottom_layers', '—')}")
    st.markdown("</div></div>", unsafe_allow_html=True)

    # Material
    st.markdown('<div class="sb-section">', unsafe_allow_html=True)
    st.markdown('<div class="sb-section-title">🧪 Material Recommendation</div>', unsafe_allow_html=True)
    rec = material.get("recommended", "—")
    reason = material.get("reason", "")
    alts = material.get("alternatives", [])
    st.markdown(f"**Recommended:** {rec}")
    if reason:
        st.markdown(f"**Why:** {reason}")
    if alts:
        st.markdown(f"**Alternatives:** {', '.join(alts)}")
    st.markdown("</div>", unsafe_allow_html=True)

    # Orientation
    st.markdown('<div class="sb-section">', unsafe_allow_html=True)
    st.markdown('<div class="sb-section-title">🧭 Orientation & Support Strategy</div>', unsafe_allow_html=True)
    st.markdown(f"**Recommended:** {orientation.get('recommended', '—')}")
    if orientation.get("reason"):
        st.markdown(f"**Why:** {orientation.get('reason')}")
    tradeoffs = orientation.get("tradeoffs", [])
    if tradeoffs:
        st.markdown("**Trade-offs:**")
        st.markdown("<ul class='sb-bullets'>" + "".join([f"<li>{t}</li>" for t in tradeoffs]) + "</ul>", unsafe_allow_html=True)
    tips = orientation.get("bed_adhesion_tips", [])
    if tips:
        st.markdown("**Bed adhesion tips:**")
        st.markdown("<ul class='sb-bullets'>" + "".join([f"<li>{t}</li>" for t in tips]) + "</ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Risks
    st.markdown('<div class="sb-section">', unsafe_allow_html=True)
    st.markdown('<div class="sb-section-title">⚠️ Risks & Mitigations</div>', unsafe_allow_html=True)
    items = risks.get("items", [])
    if not items:
        st.markdown("**Risks:** None detected.")
    else:
        for it in items:
            st.markdown(f"- **{it.get('severity','').upper()}** — {it.get('why','')}")
        mitigations = risks.get("mitigations", [])
        if mitigations:
            st.markdown("**Mitigations:**")
            st.markdown("<ul class='sb-bullets'>" + "".join([f"<li>{m}</li>" for m in mitigations]) + "</ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)


# =========================
# SIDEBAR (matches reference layout)
# =========================
with st.sidebar:
    st.markdown("### SliceBuddy")
    if st.button("➕  New Print Plan", use_container_width=True):
        st.session_state.active_idx = None

    st.markdown("#### RECENT PLANS")
    if not st.session_state.plans:
        st.caption("No plans yet.")
    else:
        for i, p in enumerate(reversed(st.session_state.plans)):
            idx = len(st.session_state.plans) - 1 - i
            title = p["title"]
            ts = p["ts"]
            label = f"{title}\n\n{ts}"
            if st.button(label, key=f"plan_{idx}", use_container_width=True):
                st.session_state.active_idx = idx


# =========================
# MAIN HEADER (green top bar)
# =========================
active = st.session_state.active_idx
active_title = "New Print Plan" if active is None else st.session_state.plans[active]["title"]

st.markdown(
    f"""
<div class="sb-topbar">
  <div class="left">
    <div class="sb-logo">SB</div>
    <div>
      <div class="sb-title">{active_title}</div>
      <div class="sb-sub">Local • LangGraph + RAG • FastAPI</div>
    </div>
    <div class="sb-badge">Active</div>
  </div>
  <div class="sb-actions">
    <div class="sb-iconbtn">⤴︎</div>
    <div class="sb-iconbtn">⬇︎</div>
    <div class="sb-iconbtn">⋮</div>
  </div>
</div>
""",
    unsafe_allow_html=True
)


# =========================
# CHAT THREAD
# =========================
st.markdown('<div class="sb-chat-wrap">', unsafe_allow_html=True)

if active is None:
    # Empty state prompt (like a fresh chat)
    st.info("Describe your 3D model in one message. Include dimensions like: **height 120 width 30**.")
else:
    p = st.session_state.plans[active]
    st.markdown(f"""
    <div class="sb-user"><div class="bubble">{p["user_text"]}</div></div>
    """, unsafe_allow_html=True)
    render_plan(p["result"])

st.markdown("</div>", unsafe_allow_html=True)


# =========================
# STICKY BOTTOM BAR (green) + chat input
# =========================
st.markdown(
    f"""
<div class="sb-bottombar">
  <div class="sb-bottom-inner">
    <div class="sb-hint">Tip: type a single message like “functional bracket, small footprint, needs strength, height 120 width 30”</div>
  </div>
</div>
""",
    unsafe_allow_html=True
)

user_msg = st.chat_input("Describe your 3D model and include dimensions (e.g. height 120 width 30).")

if user_msg:
    with st.spinner("Planning your print..."):
        result = call_backend(user_msg)

    new_item = {
        "title": extract_title(user_msg),
        "ts": time.strftime("%b %d • %H:%M"),
        "user_text": user_msg,
        "result": result,
    }
    st.session_state.plans.append(new_item)
    st.session_state.active_idx = len(st.session_state.plans) - 1
    st.rerun()