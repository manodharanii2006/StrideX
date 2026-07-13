"""StrideX — professional Streamlit medtech research prototype.

Run from the project root:
    streamlit run app.py

The application is intentionally described as a screening and monitoring
prototype. It does not diagnose neurological or musculoskeletal disease.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
import hashlib
import time
from typing import Any, Mapping, Sequence

import pandas as pd
import streamlit as st

from backend import (
    APP_VERSION,
    DISCLAIMER,
    build_report_html,
    create_assessment_record,
    get_ai_insights,
    get_capabilities,
    get_dashboard_alerts,
    get_dashboard_statistics,
    get_device_status,
    get_recent_assessments,
    get_simulated_sensor_data,
    get_weekly_trend,
    history_to_csv,
    make_demo_history,
    process_gait_images,
    process_gait_video,
    run_full_stridex_analysis,
)

try:
    import plotly.graph_objects as go

    HAS_PLOTLY = True
except Exception:
    go = None
    HAS_PLOTLY = False


st.set_page_config(
    page_title="StrideX | Mobility Risk Assessment",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# Visual system
# =============================================================================

def inject_styles() -> None:
    st.markdown(
        """
<style>
:root {
    --sx-bg: #07111f;
    --sx-bg-soft: #0b1728;
    --sx-panel: rgba(14, 31, 51, 0.88);
    --sx-panel-strong: #102238;
    --sx-border: rgba(158, 184, 207, 0.18);
    --sx-border-strong: rgba(111, 204, 221, 0.38);
    --sx-text: #eef7fb;
    --sx-text-soft: #b2c5d3;
    --sx-muted: #7891a5;
    --sx-blue: #5d9cec;
    --sx-teal: #77b8f4;
    --sx-green: #5fd7a1;
    --sx-amber: #f4a261;
    --sx-orange: #f4a261;
    --sx-orange-soft: #ffd2aa;
    --sx-red: #ff7c8a;
    --sx-radius: 14px;
    --sx-shadow: 0 16px 42px rgba(0, 0, 0, 0.24);
}

html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                 "Segoe UI", sans-serif !important;
}

.stApp {
    color: var(--sx-text);
    background:
      radial-gradient(circle at 16% -10%, rgba(46, 130, 197, 0.23), transparent 34rem),
      radial-gradient(circle at 92% 8%, rgba(244, 162, 97, 0.12), transparent 31rem),
      linear-gradient(180deg, #07111f 0%, #07101d 100%);
}

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] {
    background: rgba(7, 17, 31, 0.76);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(158, 184, 207, 0.08);
}

.block-container {
    max-width: 1460px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #091528 0%, #07111f 100%);
    border-right: 1px solid var(--sx-border);
}
[data-testid="stSidebar"] .block-container { padding-top: 1.25rem; }
[data-testid="stSidebar"] hr { border-color: var(--sx-border); }

h1, h2, h3, h4, p, label, .stMarkdown { color: var(--sx-text); }
a { color: #7bd4ff !important; }
small, .stCaption { color: var(--sx-muted) !important; }

/* Native bordered containers become dependable widget cards. */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(16, 34, 56, 0.93), rgba(11, 25, 42, 0.93));
    border: 1px solid var(--sx-border) !important;
    border-radius: var(--sx-radius) !important;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.15);
}

div[data-testid="stMetric"] {
    background: linear-gradient(180deg, rgba(18, 40, 65, 0.92), rgba(12, 27, 46, 0.92));
    border: 1px solid var(--sx-border);
    border-radius: var(--sx-radius);
    padding: 1rem 1.05rem;
    min-height: 118px;
}
div[data-testid="stMetricLabel"] { color: var(--sx-muted); }
div[data-testid="stMetricValue"] { color: var(--sx-text); }

.stButton > button,
.stDownloadButton > button,
button[kind="primary"] {
    min-height: 42px;
    border-radius: 10px !important;
    border: 1px solid rgba(93, 156, 236, 0.46) !important;
    background: linear-gradient(135deg, #5d9cec, #3e78b6) !important;
    color: white !important;
    font-weight: 700 !important;
    box-shadow: 0 9px 22px rgba(53, 116, 177, 0.20);
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: rgba(244, 162, 97, 0.78) !important;
    filter: brightness(1.08);
    transform: translateY(-1px);
}
.stButton > button:disabled { opacity: 0.46; transform: none; }

button:focus-visible,
input:focus-visible,
textarea:focus-visible,
[role="radio"]:focus-visible,
[role="slider"]:focus-visible {
    outline: 3px solid rgba(244, 162, 97, 0.72) !important;
    outline-offset: 2px !important;
}

input, textarea, [data-baseweb="select"] > div {
    background: rgba(8, 20, 35, 0.8) !important;
    color: var(--sx-text) !important;
    border-color: var(--sx-border) !important;
    border-radius: 10px !important;
}

[data-testid="stFileUploader"] {
    background: rgba(8, 20, 35, 0.56);
    border-radius: 12px;
    padding: 0.4rem;
}
[data-testid="stFileUploaderDropzone"] {
    background: rgba(90, 183, 245, 0.045) !important;
    border-color: rgba(90, 183, 245, 0.26) !important;
    border-radius: 12px !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--sx-border);
    border-radius: 12px;
    overflow: hidden;
}

[data-testid="stAlert"] { border-radius: 12px; }

/* Sidebar navigation */
[data-testid="stSidebar"] div[role="radiogroup"] { gap: 0.25rem; }
[data-testid="stSidebar"] label[data-baseweb="radio"] {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 0.55rem 0.65rem;
    transition: background 140ms ease, border-color 140ms ease;
}
[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
    background: rgba(90, 183, 245, 0.07);
    border-color: var(--sx-border);
}

.sx-brand {
    padding: 0.45rem 0.3rem 1rem;
    border-bottom: 1px solid var(--sx-border);
    margin-bottom: 1rem;
}
.sx-brand-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 38px; height: 38px;
    border-radius: 12px;
    margin-right: 0.65rem;
    background: linear-gradient(135deg, rgba(93,156,236,.28), rgba(244,162,97,.16));
    border: 1px solid rgba(244,162,97,.34);
    color: #b9dcff;
    font-weight: 800;
}
.sx-brand-title { font-size: 1.08rem; font-weight: 800; letter-spacing: -0.02em; }
.sx-brand-sub { color: var(--sx-muted); font-size: 0.72rem; margin-top: 0.15rem; }
.sx-user-card {
    background: rgba(255,255,255,.025);
    border: 1px solid var(--sx-border);
    border-radius: 12px;
    padding: 0.8rem 0.9rem;
    margin-bottom: 0.9rem;
}
.sx-user-role { color: var(--sx-teal); font-size: .68rem; letter-spacing: .08em; text-transform: uppercase; }
.sx-user-name { color: var(--sx-text); font-size: .88rem; font-weight: 700; margin-top: .2rem; }
.sx-side-label { color: var(--sx-muted); font-size: .68rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; margin: .75rem 0 .35rem; }
.sx-status-line { color: var(--sx-text-soft); font-size: .76rem; margin: .38rem 0; }
.sx-status-dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--sx-green); box-shadow:0 0 8px rgba(95,215,161,.68); margin-right:.48rem; }
.sx-status-dot.warn { background:var(--sx-amber); box-shadow:0 0 8px rgba(245,199,107,.54); }

.sx-page-header { margin-bottom: 1.35rem; }
.sx-eyebrow { color: var(--sx-teal); font-size: .7rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
.sx-page-title { color: var(--sx-text); font-size: clamp(1.65rem, 3vw, 2.25rem); font-weight: 800; letter-spacing: -.035em; line-height: 1.14; margin-top: .28rem; }
.sx-page-desc { color: var(--sx-text-soft); font-size: .93rem; max-width: 820px; line-height: 1.65; margin-top: .5rem; }

.sx-banner {
    display: flex; align-items: flex-start; gap: .8rem;
    border: 1px solid rgba(245,199,107,.32);
    background: rgba(245,199,107,.075);
    border-radius: 12px;
    padding: .9rem 1rem;
    margin: .35rem 0 1.3rem;
}
.sx-banner strong { color: #ffe6aa; }
.sx-banner-text { color: #d5c69f; font-size: .82rem; line-height: 1.55; }

.sx-kpi {
    position: relative;
    min-height: 126px;
    overflow: hidden;
    background: linear-gradient(160deg, rgba(18,41,67,.98), rgba(10,24,42,.96));
    border: 1px solid var(--sx-border);
    border-radius: var(--sx-radius);
    padding: 1rem 1.05rem;
    box-shadow: var(--sx-shadow);
}
.sx-kpi:after { content:""; position:absolute; right:-28px; top:-34px; width:90px; height:90px; border-radius:50%; background:rgba(90,183,245,.08); }
.sx-kpi-label { color:var(--sx-muted); font-size:.68rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
.sx-kpi-value { color:var(--sx-text); font-size:1.8rem; line-height:1.1; font-weight:800; margin-top:.55rem; letter-spacing:-.04em; }
.sx-kpi-detail { color:var(--sx-text-soft); font-size:.74rem; margin-top:.45rem; }
.sx-kpi.high { border-color:rgba(255,124,138,.30); }
.sx-kpi.medium { border-color:rgba(245,199,107,.30); }
.sx-kpi.good { border-color:rgba(95,215,161,.28); }

.sx-section-title { color:var(--sx-text); font-size:1rem; font-weight:800; margin: .1rem 0 .75rem; }
.sx-section-kicker { color:var(--sx-orange); font-size:.67rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
.sx-muted { color:var(--sx-muted); }

.sx-alert-item {
    display:grid; grid-template-columns:auto 1fr; gap:.72rem;
    padding:.78rem 0; border-bottom:1px solid rgba(158,184,207,.10);
}
.sx-alert-item:last-child { border-bottom:none; }
.sx-alert-badge { min-width:70px; text-align:center; padding:.32rem .5rem; border-radius:999px; font-size:.66rem; font-weight:800; letter-spacing:.06em; }
.sx-alert-badge.high { background:rgba(255,124,138,.11); border:1px solid rgba(255,124,138,.33); color:#ff9aa5; }
.sx-alert-badge.medium { background:rgba(245,199,107,.10); border:1px solid rgba(245,199,107,.30); color:#f8d890; }
.sx-alert-main { color:var(--sx-text); font-size:.82rem; font-weight:700; }
.sx-alert-sub { color:var(--sx-muted); font-size:.73rem; margin-top:.18rem; line-height:1.4; }

.sx-empty {
    text-align:center; padding:2.2rem 1rem;
    border:1px dashed rgba(158,184,207,.22);
    border-radius:12px; color:var(--sx-muted);
    background:rgba(255,255,255,.015);
}
.sx-empty-title { color:var(--sx-text-soft); font-weight:800; margin-bottom:.35rem; }

.sx-chip { display:inline-flex; align-items:center; padding:.28rem .55rem; border-radius:999px; font-size:.68rem; font-weight:800; border:1px solid var(--sx-border); color:var(--sx-text-soft); background:rgba(255,255,255,.025); }
.sx-chip.green { color:#93ebbd; border-color:rgba(95,215,161,.3); background:rgba(95,215,161,.07); }
.sx-chip.amber { color:#f7d991; border-color:rgba(245,199,107,.3); background:rgba(245,199,107,.07); }
.sx-chip.blue { color:#9bd9ff; border-color:rgba(90,183,245,.3); background:rgba(90,183,245,.07); }

.sx-priority {
    display:inline-flex; align-items:center; gap:.45rem;
    border-radius:999px; padding:.42rem .75rem;
    font-size:.72rem; font-weight:900; letter-spacing:.06em;
}
.sx-priority.low { color:#91e7b8; background:rgba(95,215,161,.09); border:1px solid rgba(95,215,161,.33); }
.sx-priority.medium { color:#f5d68c; background:rgba(245,199,107,.09); border:1px solid rgba(245,199,107,.33); }
.sx-priority.high { color:#ff9ca7; background:rgba(255,124,138,.09); border:1px solid rgba(255,124,138,.36); }

.sx-score-wrap { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; }
.sx-score { font-size:2.65rem; font-weight:850; letter-spacing:-.06em; color:var(--sx-text); line-height:1; }
.sx-score small { color:var(--sx-muted); font-size:.8rem; letter-spacing:0; }
.sx-meter { height:9px; border-radius:999px; background:rgba(255,255,255,.07); overflow:hidden; margin:.85rem 0 .35rem; }
.sx-meter > div { height:100%; border-radius:inherit; background:linear-gradient(90deg,#5d9cec,#7ab6ef); }
.sx-meter.high > div { background:linear-gradient(90deg,#f4a261,#ef7d6f); }
.sx-meter.medium > div { background:linear-gradient(90deg,#5d9cec,#f4a261); }

.sx-factor { margin:.85rem 0; }
.sx-factor-top { display:flex; justify-content:space-between; gap:1rem; font-size:.78rem; color:var(--sx-text-soft); }
.sx-factor-track { height:6px; border-radius:999px; background:rgba(255,255,255,.065); margin-top:.38rem; overflow:hidden; }
.sx-factor-fill { height:100%; border-radius:999px; background:linear-gradient(90deg,#5d9cec,#f4a261); }

.sx-workflow { display:grid; grid-template-columns:repeat(6,minmax(120px,1fr)); gap:.6rem; }
.sx-step { position:relative; padding:.9rem .75rem; min-height:96px; border:1px solid var(--sx-border); border-radius:12px; background:rgba(255,255,255,.02); }
.sx-step-num { color:var(--sx-orange); font-size:.66rem; font-weight:900; letter-spacing:.1em; }
.sx-step-title { color:var(--sx-text); font-size:.78rem; font-weight:800; margin-top:.45rem; }
.sx-step-sub { color:var(--sx-muted); font-size:.68rem; line-height:1.35; margin-top:.22rem; }

.sx-mode-card { border:1px solid var(--sx-border); background:rgba(255,255,255,.02); border-radius:12px; padding:.9rem 1rem; }
.sx-mode-title { color:var(--sx-text); font-weight:800; font-size:.84rem; }
.sx-mode-text { color:var(--sx-text-soft); font-size:.75rem; line-height:1.5; margin-top:.25rem; }

.sx-auth-title { font-size:1.55rem; font-weight:850; letter-spacing:-.04em; }
.sx-auth-sub { color:var(--sx-text-soft); font-size:.85rem; line-height:1.55; margin-top:.4rem; }

@media (max-width: 900px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .sx-workflow { grid-template-columns:repeat(2,minmax(0,1fr)); }
}
@media (max-width: 560px) {
    .sx-page-title { font-size:1.55rem; }
    .sx-workflow { grid-template-columns:1fr; }
    .sx-score { font-size:2.1rem; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { scroll-behavior:auto !important; transition:none !important; animation:none !important; }
}

/* Mild orange + blue interaction layer */
[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked),
label[data-baseweb="radio"]:has(input:checked) {
    background: linear-gradient(90deg, rgba(93,156,236,.12), rgba(244,162,97,.08));
    border-color: rgba(244,162,97,.34) !important;
}
label[data-baseweb="radio"]:has(input:checked) p { color: #f9fbff !important; font-weight: 750; }
label[data-baseweb="radio"]:has(input:checked) > div:first-child {
    border-color: var(--sx-orange) !important;
}
label[data-baseweb="radio"]:has(input:checked) > div:first-child > div {
    background-color: var(--sx-orange) !important;
}

div[data-baseweb="slider"] div[role="slider"] {
    background-color: var(--sx-orange) !important;
    border-color: #ffe0c1 !important;
    box-shadow: 0 0 0 4px rgba(244,162,97,.15) !important;
}
div[data-baseweb="slider"] [data-testid="stTickBar"] { color: var(--sx-muted) !important; }

.sx-input-note {
    border-left: 3px solid var(--sx-blue);
    background: rgba(93,156,236,.065);
    color: var(--sx-text-soft);
    border-radius: 9px;
    padding: .72rem .85rem;
    font-size: .78rem;
    line-height: 1.55;
}
.sx-threshold-grid {
    display:grid;
    grid-template-columns:repeat(3,minmax(0,1fr));
    gap:.6rem;
    margin-top:.8rem;
}
.sx-threshold {
    border:1px solid var(--sx-border);
    border-radius:10px;
    padding:.7rem .75rem;
    background:rgba(255,255,255,.018);
}
.sx-threshold strong { display:block; font-size:.72rem; margin-bottom:.24rem; }
.sx-threshold span { color:var(--sx-muted); font-size:.68rem; line-height:1.4; }
.sx-threshold.low strong { color:#91e7b8; }
.sx-threshold.medium strong { color:#ffc786; }
.sx-threshold.high strong { color:#ff9ca7; }

.sx-result-alert {
    border-radius:12px;
    padding:.9rem 1rem;
    margin:.15rem 0 1rem;
    border:1px solid var(--sx-border);
    background:rgba(93,156,236,.055);
}
.sx-result-alert.high { border-color:rgba(255,124,138,.38); background:rgba(255,124,138,.075); }
.sx-result-alert.medium { border-color:rgba(244,162,97,.38); background:rgba(244,162,97,.075); }
.sx-result-alert.low { border-color:rgba(93,156,236,.36); background:rgba(93,156,236,.065); }
.sx-result-alert-title { font-size:.76rem; font-weight:900; letter-spacing:.08em; text-transform:uppercase; }
.sx-result-alert.high .sx-result-alert-title { color:#ff9ca7; }
.sx-result-alert.medium .sx-result-alert-title { color:#ffc786; }
.sx-result-alert.low .sx-result-alert-title { color:#9cc9ff; }
.sx-result-alert-text { color:var(--sx-text-soft); font-size:.78rem; margin-top:.28rem; line-height:1.5; }

.sx-reading-grid {
    display:grid;
    grid-template-columns:repeat(4,minmax(0,1fr));
    gap:.65rem;
    margin:.8rem 0 .3rem;
}
.sx-reading {
    border:1px solid var(--sx-border);
    border-radius:10px;
    padding:.72rem .78rem;
    background:rgba(255,255,255,.018);
}
.sx-reading-label { color:var(--sx-muted); font-size:.64rem; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }
.sx-reading-value { color:var(--sx-text); font-size:1rem; font-weight:800; margin-top:.28rem; }
.sx-reading-value.blue { color:#9cc9ff; }
.sx-reading-value.orange { color:#ffc786; }

@media (max-width: 760px) {
    .sx-threshold-grid, .sx-reading-grid { grid-template-columns:1fr; }
}

</style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# State and navigation
# =============================================================================

def init_state() -> None:
    defaults: dict[str, Any] = {
        "logged_in": False,
        "username": "",
        "auth_page": "login",
        "nav_page": "Dashboard",
        # Start with clearly labelled simulated records so the dashboard is
        # immediately populated for the hackathon demonstration. New analyses
        # are appended to this same list and therefore update every dashboard KPI.
        "history": make_demo_history(),
        "last_result": None,
        "pose_result": None,
        "pose_signature": None,
        "sensor_data": get_simulated_sensor_data(True, seed=4201),
        "share_log": [],
        "users": {
            "admin": {
                "password": "admin123",
                "name": "Demo Clinical Lead",
                "role": "Clinical Lead",
            }
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def navigate_to(page: str) -> None:
    st.session_state["nav_page"] = page


def sign_out() -> None:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["auth_page"] = "login"


def clear_pose_result() -> None:
    st.session_state["pose_result"] = None
    st.session_state["pose_signature"] = None


def file_signature(files: Sequence[Any]) -> str:
    parts = []
    for item in files:
        if item is None:
            continue
        parts.append(f"{getattr(item, 'name', 'file')}:{getattr(item, 'size', 0)}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest() if parts else ""


def safe_filename(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)
    return cleaned.strip("_") or "stridex_report"


init_state()
inject_styles()


# =============================================================================
# Reusable visual helpers
# =============================================================================

def page_header(eyebrow: str, title: str, description: str) -> None:
    st.markdown(
        f"""
<div class="sx-page-header">
  <div class="sx-eyebrow">{escape(eyebrow)}</div>
  <div class="sx-page-title">{escape(title)}</div>
  <div class="sx-page-desc">{escape(description)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def prototype_banner() -> None:
    st.markdown(
        f"""
<div class="sx-banner">
  <div aria-hidden="true">⚠</div>
  <div class="sx-banner-text"><strong>Research prototype — not a diagnostic device.</strong>
  {escape(DISCLAIMER)} Current scoring thresholds are transparent demonstration rules and require clinical validation.</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, detail: str, tone: str = "") -> None:
    st.markdown(
        f"""
<div class="sx-kpi {escape(tone)}">
  <div class="sx-kpi-label">{escape(label)}</div>
  <div class="sx-kpi-value">{escape(value)}</div>
  <div class="sx-kpi-detail">{escape(detail)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(title: str, detail: str) -> None:
    st.markdown(
        f"""
<div class="sx-empty">
  <div class="sx-empty-title">{escape(title)}</div>
  <div>{escape(detail)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def priority_badge(priority: str, label: str | None = None) -> str:
    normalized = priority.upper()
    text = label or normalized
    return f'<span class="sx-priority {normalized.lower()}">{escape(text)}</span>'


def render_factor_bars(factors: Sequence[Mapping[str, Any]]) -> None:
    if not factors:
        st.caption("No factor details are available for this assessment.")
        return
    for factor in sorted(factors, key=lambda item: float(item.get("value", 0)), reverse=True):
        value = max(0, min(100, int(float(factor.get("value", 0)))))
        st.markdown(
            f"""
<div class="sx-factor">
  <div class="sx-factor-top">
    <span>{escape(str(factor.get('label', 'Factor')))}</span>
    <span>{value}/100 · {escape(str(factor.get('source', 'input')))}</span>
  </div>
  <div class="sx-factor-track"><div class="sx-factor-fill" style="width:{value}%"></div></div>
</div>
            """,
            unsafe_allow_html=True,
        )


def plot_risk_distribution(history: Sequence[Mapping[str, Any]]) -> None:
    stats = get_dashboard_statistics(history)
    labels = ["Routine", "Follow-up", "Prompt review"]
    values = [stats["low"], stats["medium"], stats["high"]]
    if not sum(values):
        empty_state("No distribution yet", "Complete an assessment or load labelled sample data.")
        return

    if HAS_PLOTLY:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.67,
                    sort=False,
                    marker=dict(colors=["#5fd7a1", "#f5c76b", "#ff7c8a"], line=dict(color="#0b1728", width=3)),
                    textinfo="percent",
                    hovertemplate="%{label}: %{value}<extra></extra>",
                )
            ]
        )
        fig.update_layout(
            height=290,
            margin=dict(l=5, r=5, t=10, b=5),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#b2c5d3", size=12),
            legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center"),
            showlegend=True,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        frame = pd.DataFrame({"Priority": labels, "Assessments": values}).set_index("Priority")
        st.bar_chart(frame)


def plot_weekly_trend(history: Sequence[Mapping[str, Any]]) -> None:
    trend = get_weekly_trend(history)
    available = [row for row in trend if row["average_concern"] is not None]
    if not available:
        empty_state("No trend data yet", "Trend lines appear after assessments are recorded across the session.")
        return

    labels = [row["label"] for row in trend]
    values = [row["average_concern"] for row in trend]
    if HAS_PLOTLY:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=labels,
                y=values,
                mode="lines+markers",
                connectgaps=False,
                line=dict(color="#5d9cec", width=3),
                marker=dict(size=8, color="#52d1c7", line=dict(color="#0b1728", width=2)),
                hovertemplate="%{x}: %{y:.0f}/100<extra></extra>",
            )
        )
        fig.update_layout(
            height=290,
            margin=dict(l=12, r=12, t=10, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#b2c5d3", size=12),
            yaxis=dict(range=[0, 100], title="Concern score", gridcolor="rgba(158,184,207,.10)"),
            xaxis=dict(gridcolor="rgba(158,184,207,.06)"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        frame = pd.DataFrame(
            {"Day": labels, "Concern score": [value if value is not None else float("nan") for value in values]}
        ).set_index("Day")
        st.line_chart(frame)


def workflow_strip() -> None:
    steps = [
        ("01", "Guided capture", "Video, images, or manual inputs"),
        ("02", "Pose estimation", "33-landmark model when available"),
        ("03", "Feature extraction", "Symmetry and stability indicators"),
        ("04", "Screening rules", "Transparent concern scoring"),
        ("05", "Explanation", "Visible contributing factors"),
        ("06", "Follow-up", "Report and longitudinal history"),
    ]
    blocks = "".join(
        f"""<div class="sx-step"><div class="sx-step-num">{num}</div>
        <div class="sx-step-title">{escape(title)}</div><div class="sx-step-sub">{escape(sub)}</div></div>"""
        for num, title, sub in steps
    )
    st.markdown(f'<div class="sx-workflow">{blocks}</div>', unsafe_allow_html=True)


# =============================================================================
# Authentication
# =============================================================================

def show_login() -> None:
    spacer_left, center, spacer_right = st.columns([1, 1.15, 1])
    with center:
        with st.container(border=True):
            st.markdown(
                """
<div class="sx-auth-title">StrideX</div>
<div class="sx-auth-sub">Clinical mobility screening and longitudinal monitoring research prototype.</div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("#### Sign in")
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Enter username")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("Sign in", use_container_width=True)
            if submitted:
                user = st.session_state["users"].get(username)
                if user and user["password"] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.rerun()
                else:
                    st.error("The username or password is incorrect.")
            st.caption("Demo access: admin / admin123. Accounts are stored only in this browser session.")
            if st.button("Create a demo account", use_container_width=True, key="auth_create_demo_account"):
                st.session_state["auth_page"] = "signup"
                st.rerun()
        prototype_banner()


def show_signup() -> None:
    spacer_left, center, spacer_right = st.columns([1, 1.15, 1])
    with center:
        with st.container(border=True):
            st.markdown('<div class="sx-auth-title">Create demo account</div>', unsafe_allow_html=True)
            st.caption("For prototype demonstrations only. This is not production authentication.")
            with st.form("signup_form"):
                full_name = st.text_input("Display name", placeholder="e.g., Dr. Ananya Iyer")
                username = st.text_input("Username")
                role = st.selectbox("Role", ["Clinician", "Physiotherapist", "Researcher", "Administrator"])
                password = st.text_input("Password", type="password")
                confirmation = st.text_input("Confirm password", type="password")
                submitted = st.form_submit_button("Create account", use_container_width=True)
            if submitted:
                if not full_name.strip() or not username.strip() or not password:
                    st.error("Complete all required fields.")
                elif len(password) < 6:
                    st.error("Use a password with at least 6 characters.")
                elif password != confirmation:
                    st.error("Passwords do not match.")
                elif username in st.session_state["users"]:
                    st.error("That username already exists in this session.")
                else:
                    st.session_state["users"][username] = {
                        "password": password,
                        "name": full_name.strip(),
                        "role": role,
                    }
                    st.success("Account created. Return to sign in.")
            if st.button("Back to sign in", use_container_width=True, key="auth_back_to_signin"):
                st.session_state["auth_page"] = "login"
                st.rerun()


# =============================================================================
# Sidebar
# =============================================================================

def render_sidebar() -> str:
    capabilities = get_capabilities()
    user = st.session_state["users"].get(st.session_state["username"], {})
    with st.sidebar:
        st.markdown(
            """
<div class="sx-brand">
  <div style="display:flex;align-items:center;">
    <div class="sx-brand-mark">SX</div>
    <div><div class="sx-brand-title">StrideX</div><div class="sx-brand-sub">Mobility screening & risk analysis</div></div>
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
<div class="sx-user-card">
  <div class="sx-user-role">{escape(str(user.get('role', 'User')))}</div>
  <div class="sx-user-name">{escape(str(user.get('name', st.session_state['username'])))}</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sx-side-label">Workspace</div>', unsafe_allow_html=True)
        page = st.radio(
            "Workspace navigation",
            ["Dashboard", "Assessment", "Patient History", "Care Network", "About"],
            key="nav_page",
            label_visibility="collapsed",
        )

        st.divider()
        pose_status = "Real pose engine ready" if capabilities["real_pose_pipeline_available"] else "Pose demo fallback"
        pose_class = "" if capabilities["real_pose_pipeline_available"] else "warn"
        st.markdown(
            f"""
<div class="sx-side-label">System status</div>
<div class="sx-status-line"><span class="sx-status-dot {pose_class}"></span>{escape(pose_status)}</div>
<div class="sx-status-line"><span class="sx-status-dot warn"></span>Wearable data is simulated</div>
<div class="sx-status-line"><span class="sx-status-dot"></span>Session-local records active</div>
<div class="sx-status-line"><span class="sx-status-dot"></span>Report generator ready</div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        st.button("Sign out", use_container_width=True, on_click=sign_out, key="sidebar_sign_out")
        st.caption(f"Version {APP_VERSION} · Research build")
    return page


# =============================================================================
# Dashboard
# =============================================================================

def render_alerts(history: Sequence[Mapping[str, Any]]) -> None:
    alerts = get_dashboard_alerts(history)
    if not alerts:
        empty_state("No active follow-up items", "High- and medium-priority assessments will appear here.")
        return
    blocks = []
    for item in alerts:
        priority = str(item["priority"]).upper()
        blocks.append(
            f"""
<div class="sx-alert-item">
  <div class="sx-alert-badge {priority.lower()}">{escape(priority)}</div>
  <div><div class="sx-alert-main">{escape(str(item['patient']))}</div>
  <div class="sx-alert-sub">{escape(str(item['message']))} · {escape(str(item['time']))}</div></div>
</div>
            """
        )
    st.markdown("".join(blocks), unsafe_allow_html=True)


def show_dashboard() -> None:
    page_header(
        "Clinical intelligence dashboard",
        "Mobility screening overview",
        "Review assessment activity, screening priorities, longitudinal patterns, and system readiness from one accessible workspace.",
    )
    prototype_banner()

    history = st.session_state["history"]
    stats = get_dashboard_statistics(history)
    insights = get_ai_insights(history)

    demo_count = sum(1 for record in history if record.get("is_demo"))
    live_count = len(history) - demo_count
    if demo_count:
        st.info(
            f"Dashboard source: {demo_count} simulated demonstration record(s) and "
            f"{live_count} assessment record(s) created during this session. "
            "Every successful analysis is appended automatically."
        )

    k1, k2, k3, k4, k5 = st.columns(5, gap="small")
    with k1:
        kpi_card("Assessments", f"{stats['total']:02d}", f"{stats['today']} recorded today")
    with k2:
        kpi_card("Prompt review", f"{stats['high']:02d}", "High-priority screening", "high")
    with k3:
        kpi_card("Follow-up", f"{stats['medium']:02d}", "Medium-priority screening", "medium")
    with k4:
        kpi_card("Average concern", f"{stats['average_concern']}/100", "Higher means more concern")
    with k5:
        kpi_card("Pose-supported", f"{stats['pose_sessions']:02d}", "Includes real or demo pose output", "good")

    st.markdown("### Screening activity")
    trend_col, alert_col = st.columns([1.7, 1], gap="large")
    with trend_col:
        with st.container(border=True):
            st.markdown('<div class="sx-section-kicker">Longitudinal view</div><div class="sx-section-title">Seven-day concern trend</div>', unsafe_allow_html=True)
            plot_weekly_trend(history)
    with alert_col:
        with st.container(border=True):
            st.markdown('<div class="sx-section-kicker">Follow-up queue</div><div class="sx-section-title">Attention items</div>', unsafe_allow_html=True)
            render_alerts(history)

    distribution_col, insight_col = st.columns([1, 1.35], gap="large")
    with distribution_col:
        with st.container(border=True):
            st.markdown('<div class="sx-section-kicker">Cohort summary</div><div class="sx-section-title">Priority distribution</div>', unsafe_allow_html=True)
            plot_risk_distribution(history)
    with insight_col:
        with st.container(border=True):
            st.markdown('<div class="sx-section-kicker">Session-derived indicators</div><div class="sx-section-title">Assessment insights</div>', unsafe_allow_html=True)
            i1, i2, i3, i4 = st.columns(4)
            i1.metric("Avg pressure", f"{insights['average_pressure']}/100")
            i2.metric("Avg pain", f"{insights['average_pain']}/10")
            i3.metric("Avg concern", f"{insights['average_concern']}/100")
            pose_quality = insights["average_pose_quality"]
            i4.metric("Avg pose quality", f"{pose_quality}%" if pose_quality is not None else "—")
            st.caption(f"Most frequent elevated factor: {insights['most_common_factor']}")

    st.markdown("### Recent assessments")
    recent = get_recent_assessments(history, limit=7)
    with st.container(border=True):
        if recent:
            st.dataframe(pd.DataFrame(recent), use_container_width=True, hide_index=True)
        else:
            empty_state("No assessments recorded", "Create an assessment or restore the simulated dashboard dataset from Quick actions.")

    st.markdown("### Quick actions")
    a1, a2, a3, a4 = st.columns(4)
    a1.button("New assessment", use_container_width=True, on_click=navigate_to, args=("Assessment",), key="dashboard_new_assessment")
    a2.button("Open patient history", use_container_width=True, on_click=navigate_to, args=("Patient History",), key="dashboard_open_history")
    a3.button("Review care network", use_container_width=True, on_click=navigate_to, args=("Care Network",), key="dashboard_care_network")
    if not history:
        if a4.button("Load labelled sample data", use_container_width=True, key="dashboard_load_sample"):
            st.session_state["history"] = make_demo_history()
            st.rerun()
    else:
        if a4.button("Reset simulated dashboard", use_container_width=True, key="dashboard_reset_sample"):
            st.session_state["history"] = make_demo_history()
            st.session_state["last_result"] = None
            st.rerun()

    st.markdown("### End-to-end workflow")
    with st.container(border=True):
        workflow_strip()


# =============================================================================
# Assessment page
# =============================================================================

def render_pose_result(result: Mapping[str, Any] | None) -> None:
    if not result:
        empty_state("No pose assessment yet", "Upload media and select Run pose assessment.")
        return
    if not result.get("success"):
        st.error(str(result.get("message", "Pose assessment failed.")))
        return

    mode = str(result.get("analysis_mode", "unknown"))
    if mode == "mediapipe":
        st.success("MediaPipe landmarks were processed from the uploaded media.")
    elif mode == "demo_fallback":
        st.warning("Demonstration fallback active: displayed gait metrics are generated, not measured.")
    else:
        st.info(str(result.get("message", "Pose result available.")))

    metrics = result.get("gait_metrics", {})
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pose quality", f"{metrics.get('pose_quality', '—')}%")
    m2.metric("Movement symmetry", f"{metrics.get('step_symmetry', '—')}%")
    m3.metric("Trunk stability", f"{metrics.get('trunk_stability_score', '—')}%")
    cadence = metrics.get("cadence_estimate")
    m4.metric("Estimated cadence", f"{cadence} steps/min" if cadence is not None else "—")

    status_steps = result.get("status_steps", [])
    if status_steps:
        st.caption("Pipeline: " + " → ".join(str(step) for step in status_steps))
    st.caption(str(result.get("message", "")))


def pose_media_section() -> Mapping[str, Any] | None:
    st.markdown("#### Optional pose-supported gait assessment")
    st.caption(
        "For real landmark processing, install compatible MediaPipe and OpenCV packages. "
        "Without them, the app remains usable but labels the output as demonstration fallback."
    )
    mode = st.radio("Media type", ["Walking video", "Two gait images"], horizontal=True, key="media_mode")

    current_files: list[Any] = []
    if mode == "Walking video":
        video = st.file_uploader(
            "Upload a 10–20 second walking video",
            type=["mp4", "mov", "avi", "m4v"],
            key="walking_video",
            help="Keep the camera still and show the full body from head to feet.",
        )
        if video:
            current_files = [video]
            st.video(video.getvalue())
    else:
        c1, c2 = st.columns(2)
        with c1:
            image_1 = st.file_uploader("Upload gait image 1", type=["jpg", "jpeg", "png"], key="gait_image_1")
        with c2:
            image_2 = st.file_uploader("Upload gait image 2", type=["jpg", "jpeg", "png"], key="gait_image_2")
        current_files = [file for file in (image_1, image_2) if file is not None]
        if current_files:
            preview_cols = st.columns(len(current_files))
            for col, item in zip(preview_cols, current_files):
                col.image(item, caption=getattr(item, "name", "Gait image"), use_column_width=True)

    signature = file_signature(current_files)
    if signature and st.session_state.get("pose_signature") not in (None, signature):
        st.info("The uploaded media has changed. Run the pose assessment again to refresh the metrics.")

    button_col, clear_col = st.columns([1, 1])
    run_clicked = button_col.button(
        "Run pose assessment",
        use_container_width=True,
        disabled=not bool(current_files),
        key="pose_run_assessment",
    )
    clear_col.button("Clear pose result", use_container_width=True, on_click=clear_pose_result, key="pose_clear_inside_media")

    if run_clicked:
        with st.spinner("Processing uploaded media..."):
            if mode == "Walking video":
                result = process_gait_video(current_files[0])
            else:
                first = current_files[0] if len(current_files) >= 1 else None
                second = current_files[1] if len(current_files) >= 2 else None
                result = process_gait_images(first, second)
        st.session_state["pose_result"] = result
        st.session_state["pose_signature"] = signature

    render_pose_result(st.session_state.get("pose_result"))
    return st.session_state.get("pose_result")


def render_assessment_result(record: Mapping[str, Any]) -> None:
    priority = str(record.get("priority", "LOW")).upper()
    score = int(record.get("concern_score", 0))
    label = str(record.get("priority_label", priority))
    base_pressure = int(record.get("pressure", 0))
    base_pain = int(record.get("pain", 0))
    adjusted_pressure = int(record.get("adjusted_pressure", base_pressure))
    adjusted_pain = int(record.get("adjusted_pain", base_pain))
    gait_applied = bool(record.get("gait_influence_applied"))

    alert_title = {
        "HIGH": "Prompt clinical review recommended",
        "MEDIUM": "Follow-up assessment recommended",
        "LOW": "Routine monitoring range",
    }.get(priority, "Review result")
    alert_text = {
        "HIGH": "The pressure or pain input crossed the high-priority prototype threshold.",
        "MEDIUM": "At least one input crossed the follow-up prototype threshold.",
        "LOW": "Both inputs remained below the follow-up prototype thresholds.",
    }.get(priority, "Review the recorded inputs.")

    with st.container(border=True):
        st.markdown(
            f"""
<div class="sx-result-alert {priority.lower()}">
  <div class="sx-result-alert-title">{escape(alert_title)}</div>
  <div class="sx-result-alert-text">{escape(alert_text)}</div>
</div>
<div class="sx-score-wrap">
  <div><div class="sx-section-kicker">Risk-analysis result</div><div style="margin-top:.45rem">{priority_badge(priority, label)}</div></div>
  <div style="text-align:right"><div class="sx-score">{score}<small>/100</small></div><div class="sx-muted" style="font-size:.72rem">Risk index</div></div>
</div>
<div class="sx-meter {priority.lower()}"><div style="width:{score}%"></div></div>
<div class="sx-reading-grid">
  <div class="sx-reading"><div class="sx-reading-label">Input pressure</div><div class="sx-reading-value blue">{base_pressure}/100</div></div>
  <div class="sx-reading"><div class="sx-reading-label">Input pain</div><div class="sx-reading-value orange">{base_pain}/10</div></div>
  <div class="sx-reading"><div class="sx-reading-label">Pressure used</div><div class="sx-reading-value blue">{adjusted_pressure}/100</div></div>
  <div class="sx-reading"><div class="sx-reading-label">Pain used</div><div class="sx-reading-value orange">{adjusted_pain}/10</div></div>
</div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "The risk category follows the original StrideX thresholds: HIGH when pressure ≥70 or pain ≥7; "
            "MEDIUM when pressure ≥40 or pain ≥4; otherwise LOW. The index is max(pressure, pain × 10)."
        )

        left, right = st.columns([1.15, 1], gap="large")
        with left:
            st.markdown("**Contributing factors**")
            render_factor_bars(record.get("factors", []))
        with right:
            st.markdown("**Clinical reasoning**")
            st.write(record.get("reason", "—"))
            st.markdown("**Recommended next step**")
            st.write(record.get("recommendation", "—"))
            source_label = "Simulated wearable demo" if record.get("input_source") == "simulated_sensor" else "Manual measurement input"
            st.caption(f"Source: {source_label} · Gait adjustment: {'Applied' if gait_applied else 'Not applied'}")

        if gait_applied and (base_pressure != adjusted_pressure or base_pain != adjusted_pain):
            st.info(
                "The optional gait indicators adjusted the values before the original pressure/pain threshold engine was applied."
            )
        if record.get("pose_analysis_mode") == "demo_fallback":
            st.warning("Pose metrics in this record came from labelled demonstration fallback, not measured landmarks.")
        if record.get("input_source") == "simulated_sensor":
            st.warning("Pressure and pain values in this record came from the simulated wearable demonstration.")

        report = build_report_html(record)
        st.download_button(
            "Download assessment report (.html)",
            data=report,
            file_name=f"{safe_filename(str(record.get('record_id', 'stridex')))}.html",
            mime="text/html",
            use_container_width=True,
        )
        st.caption("Open the HTML report in a browser and use Print → Save as PDF when a PDF copy is required.")


def show_assessment() -> None:
    page_header(
        "New screening session",
        "Mobility risk assessment",
        "Use the original StrideX pressure-and-pain risk engine inside the upgraded professional workflow, with optional pose-based gait adjustment.",
    )
    prototype_banner()

    st.markdown("### 1. Participant information")
    with st.container(border=True):
        p1, p2 = st.columns([1.15, 1], gap="large")
        with p1:
            patient_name = st.text_input("Participant name", placeholder="Use a coded or consented name")
            patient_id = st.text_input("Patient or study ID", placeholder="e.g., SX-PT-001")
        with p2:
            age_band = st.selectbox("Age band", ["Under 18", "18–29", "30–39", "40–49", "50–59", "60–69", "70–79", "80+"])
            notes = st.text_area("Session notes (optional)", placeholder="Walking aid, footwear, recent injury, capture conditions...", height=102)
        st.caption("Use de-identified participant identifiers during demonstrations whenever possible.")

    st.markdown("### 2. Clinical risk inputs")
    source_col, values_col = st.columns([0.9, 1.25], gap="large")

    with source_col:
        with st.container(border=True):
            st.markdown("#### Measurement source")
            source_mode = st.radio(
                "Choose input source",
                ["Manual measurements", "Simulated BLE insole demo"],
                index=1,
                key="measurement_source",
            )
            if source_mode == "Simulated BLE insole demo":
                if st.session_state.get("sensor_data") is None:
                    st.session_state["sensor_data"] = get_simulated_sensor_data(True)
                if st.button("Generate new simulated reading", use_container_width=True, key="sensor_generate_reading"):
                    st.session_state["sensor_data"] = get_simulated_sensor_data(True)
                sensor_data = st.session_state["sensor_data"]
                pressure = int(sensor_data["pressure"])
                pain = int(sensor_data["pain"])
                st.markdown(
                    f"""
<div class="sx-reading-grid" style="grid-template-columns:repeat(2,minmax(0,1fr));">
  <div class="sx-reading"><div class="sx-reading-label">Simulated pressure</div><div class="sx-reading-value blue">{pressure}/100</div></div>
  <div class="sx-reading"><div class="sx-reading-label">Simulated pain</div><div class="sx-reading-value orange">{pain}/10</div></div>
</div>
                    """,
                    unsafe_allow_html=True,
                )
                st.warning("Demonstration only — these values were not measured from a person or a physical device.")
            else:
                sensor_data = None
                st.markdown(
                    '<div class="sx-input-note">Enter the normalized plantar-load index and the participant-reported pain score. The values are processed by the same threshold rules used in your earlier working prototype.</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                """
<div class="sx-threshold-grid">
  <div class="sx-threshold low"><strong>LOW</strong><span>Pressure &lt; 40 and pain &lt; 4</span></div>
  <div class="sx-threshold medium"><strong>MEDIUM</strong><span>Pressure 40–69 or pain 4–6</span></div>
  <div class="sx-threshold high"><strong>HIGH</strong><span>Pressure ≥ 70 or pain ≥ 7</span></div>
</div>
                """,
                unsafe_allow_html=True,
            )

    with values_col:
        with st.container(border=True):
            st.markdown("#### Pressure and pain measurements")
            if source_mode == "Simulated BLE insole demo":
                st.slider(
                    "Plantar-load index",
                    0,
                    100,
                    pressure,
                    disabled=True,
                    help="Value supplied by the simulated wearable demo.",
                )
                st.slider(
                    "Self-reported pain (0–10)",
                    0,
                    10,
                    pain,
                    disabled=True,
                    help="Demonstration value supplied by the simulated sensor workflow.",
                )
                st.caption("Generate a new simulated reading from the source panel to change these values.")
            else:
                pressure = st.slider(
                    "Plantar-load index",
                    0,
                    100,
                    30,
                    help="Normalized prototype index. It is not a pressure unit such as kPa.",
                )
                pain = st.slider(
                    "Self-reported pain (0–10)",
                    0,
                    10,
                    2,
                    help="Participant-reported input; it is not detected by the camera or AI.",
                )
                st.caption("These values are evaluated with the original LOW / MEDIUM / HIGH threshold engine.")

    st.markdown("### 3. Optional walking-media analysis")
    with st.container(border=True):
        pose_result = pose_media_section()

    pose_ready = bool(pose_result and pose_result.get("success"))
    include_pose = st.checkbox(
        "Apply available gait indicators before the pressure/pain risk thresholds",
        value=pose_ready,
        disabled=not pose_ready,
        help=(
            "This preserves the earlier prototype behaviour: low symmetry can add 5 pressure points, "
            "instability can add 1 pain point, and low stride consistency can add 5 pressure points."
        ),
    )

    st.markdown("### 4. Run risk analysis")
    action_left, action_right = st.columns([1.6, 1])
    analyze = action_left.button("Analyze and save to dashboard", use_container_width=True, type="primary", key="assessment_analyze_save")
    action_right.button("Clear pose result", use_container_width=True, on_click=clear_pose_result, key="assessment_clear_pose")

    if analyze:
        gait_metrics = pose_result.get("gait_metrics") if include_pose and pose_result else None
        with st.spinner("Applying the original StrideX threshold engine..."):
            time.sleep(0.35)
            analysis = run_full_stridex_analysis(
                manual_pressure=pressure,
                manual_pain=pain,
                sensor_data=sensor_data,
                gait_metrics=gait_metrics,
            )
        record = create_assessment_record(
            patient_name=patient_name,
            patient_id=patient_id,
            age_band=age_band,
            analysis=analysis,
            pose_result=pose_result if include_pose else None,
            notes=notes,
            is_demo=(source_mode == "Simulated BLE insole demo")
            or bool(pose_result and pose_result.get("analysis_mode") == "demo_fallback"),
        )
        st.session_state["history"].append(record)
        st.session_state["last_result"] = record
        st.success(
            f"Assessment {record['record_id']} was saved. Dashboard totals, charts, "
            "alerts, and patient history are now updated."
        )

    if st.session_state.get("last_result"):
        st.markdown("### Result")
        render_assessment_result(st.session_state["last_result"])
        result_nav_left, result_nav_right = st.columns([1, 1])
        result_nav_left.button(
            "View updated dashboard",
            use_container_width=True,
            on_click=navigate_to,
            args=("Dashboard",),
            key="assessment_view_dashboard",
        )
        result_nav_right.button(
            "Open patient history",
            use_container_width=True,
            on_click=navigate_to,
            args=("Patient History",),
            key="assessment_open_history",
        )


# =============================================================================
# Patient history
# =============================================================================

def show_history() -> None:
    page_header(
        "Longitudinal monitoring",
        "Patient history",
        "Filter session records, compare concern scores, inspect pose provenance, and export de-identified assessment data.",
    )
    prototype_banner()

    history = list(st.session_state["history"])
    stats = get_dashboard_statistics(history)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total records", stats["total"])
    c2.metric("Prompt review", stats["high"])
    c3.metric("Follow-up", stats["medium"])
    c4.metric("Routine", stats["low"])

    if not history:
        empty_state("No patient history", "Complete an assessment or load sample data from the dashboard.")
        return

    st.markdown("### Filters")
    f1, f2, f3 = st.columns([1, 1, 1.4])
    priority_filter = f1.multiselect("Screening priority", ["LOW", "MEDIUM", "HIGH"], default=["LOW", "MEDIUM", "HIGH"])
    provenance_filter = f2.multiselect(
        "Pose provenance",
        ["mediapipe", "demo_fallback", "not_used"],
        default=["mediapipe", "demo_fallback", "not_used"],
    )
    search_term = f3.text_input("Search participant or record ID", placeholder="Type a name, ID, or record number")

    filtered = []
    for row in history:
        priority = str(row.get("priority") or row.get("risk") or "LOW").upper()
        provenance = str(row.get("pose_analysis_mode", "not_used"))
        haystack = " ".join(
            [str(row.get("patient_name", "")), str(row.get("patient_id", "")), str(row.get("record_id", ""))]
        ).lower()
        if priority not in priority_filter or provenance not in provenance_filter:
            continue
        if search_term and search_term.lower() not in haystack:
            continue
        filtered.append(row)

    trend_col, distribution_col = st.columns([1.55, 1], gap="large")
    with trend_col:
        with st.container(border=True):
            st.markdown("#### Concern-score trend")
            if filtered:
                ordered = sorted(filtered, key=lambda row: row.get("timestamp_iso", ""))
                if HAS_PLOTLY:
                    fig = go.Figure(
                        go.Scatter(
                            x=[row.get("time", "") for row in ordered],
                            y=[row.get("concern_score", 0) for row in ordered],
                            mode="lines+markers",
                            line=dict(color="#5d9cec", width=3),
                            marker=dict(color="#f4a261", size=8),
                            customdata=[row.get("patient_name", "") for row in ordered],
                            hovertemplate="%{customdata}<br>%{x}<br>Score %{y}/100<extra></extra>",
                        )
                    )
                    fig.update_layout(
                        height=300,
                        margin=dict(l=10, r=10, t=10, b=55),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#b2c5d3"),
                        yaxis=dict(range=[0, 100], gridcolor="rgba(158,184,207,.10)"),
                        xaxis=dict(gridcolor="rgba(158,184,207,.06)"),
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    frame = pd.DataFrame(
                        {"Assessment": [row.get("time", "") for row in ordered], "Concern score": [row.get("concern_score", 0) for row in ordered]}
                    ).set_index("Assessment")
                    st.line_chart(frame)
            else:
                empty_state("No matching trend", "Adjust the filters to view assessment records.")
    with distribution_col:
        with st.container(border=True):
            st.markdown("#### Priority distribution")
            plot_risk_distribution(filtered)

    st.markdown("### Assessment records")
    if filtered:
        table_rows = []
        for row in sorted(filtered, key=lambda item: item.get("timestamp_iso", ""), reverse=True):
            table_rows.append(
                {
                    "Record": row.get("record_id", "—"),
                    "Participant": row.get("patient_name", "—"),
                    "Patient ID": row.get("patient_id", "—"),
                    "Time": row.get("time", "—"),
                    "Priority": row.get("priority", "—"),
                    "Concern": row.get("concern_score", "—"),
                    "Pressure": row.get("pressure", "—"),
                    "Pain": row.get("pain", "—"),
                    "Pose mode": row.get("pose_analysis_mode", "not_used"),
                    "Demo": "Yes" if row.get("is_demo") else "No",
                }
            )
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    else:
        empty_state("No matching records", "Adjust or clear the filters.")

    st.markdown("### Record details and export")
    detail_col, export_col = st.columns([1.3, 1], gap="large")
    with detail_col:
        with st.container(border=True):
            options = [row.get("record_id") for row in filtered]
            if options:
                selected_id = st.selectbox("Select a record", options)
                selected = next(row for row in filtered if row.get("record_id") == selected_id)
                st.markdown(priority_badge(str(selected.get("priority", "LOW")), str(selected.get("priority_label", ""))), unsafe_allow_html=True)
                st.write(f"**Participant:** {selected.get('patient_name', '—')} · **Patient ID:** {selected.get('patient_id', '—')}")
                st.write(f"**Explanation:** {selected.get('reason', '—')}")
                st.write(f"**Next step:** {selected.get('recommendation', '—')}")
                report = build_report_html(selected)
                st.download_button(
                    "Download selected report (.html)",
                    data=report,
                    file_name=f"{safe_filename(str(selected_id))}.html",
                    mime="text/html",
                    use_container_width=True,
                )
            else:
                st.caption("No filtered record is available for inspection.")
    with export_col:
        with st.container(border=True):
            st.markdown("#### Session data")
            csv_data = history_to_csv(filtered)
            st.download_button(
                "Export filtered history (.csv)",
                data=csv_data,
                file_name=f"stridex_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
                disabled=not bool(filtered),
            )
            st.caption("Exports include the demo-data flag and pose provenance for auditability.")
            with st.expander("Clear all session history"):
                confirmation = st.checkbox("I understand this removes all records from the current session.")
                if st.button("Clear session history", disabled=not confirmation, use_container_width=True, key="history_clear_all"):
                    st.session_state["history"] = []
                    st.session_state["last_result"] = None
                    st.rerun()


# =============================================================================
# Care network
# =============================================================================

def show_care_network() -> None:
    page_header(
        "Care coordination",
        "Care network",
        "Demonstrate how structured mobility reports could move between patients, physiotherapists, clinicians, and community programmes.",
    )
    prototype_banner()

    st.info("No external health system is connected in this prototype. Sharing actions below are local demonstrations only.")
    partner_data = [
        ("Physiotherapy centre", "Primary pilot partner", "Uses repeated metrics to support rehabilitation follow-up and progress review."),
        ("Neurology clinic", "Referral partner", "Receives a structured screening summary when professional review is recommended."),
        ("Geriatric programme", "Community partner", "Supports repeat mobility screening for older adults and fall-risk workflows."),
        ("Research institution", "Validation partner", "Compares StrideX measurements with accepted clinical and laboratory assessments."),
    ]
    cols = st.columns(4, gap="small")
    for col, (title, type_label, description) in zip(cols, partner_data):
        with col:
            st.markdown(
                f"""
<div class="sx-mode-card" style="min-height:190px">
  <span class="sx-chip blue">{escape(type_label)}</span>
  <div class="sx-mode-title" style="margin-top:.85rem">{escape(title)}</div>
  <div class="sx-mode-text">{escape(description)}</div>
</div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Demonstration report hand-off")
    handoff_col, log_col = st.columns([1, 1], gap="large")
    with handoff_col:
        with st.container(border=True):
            last_record = st.session_state.get("last_result")
            if last_record:
                st.write(f"**Selected report:** {last_record.get('record_id')} · {last_record.get('patient_name')}")
            else:
                st.caption("Complete an assessment to select a report for hand-off.")
            recipient = st.selectbox(
                "Demonstration recipient",
                ["Physiotherapy centre", "Neurology clinic", "Geriatric programme", "Research institution"],
            )
            purpose = st.selectbox("Purpose", ["Follow-up review", "Referral support", "Research validation", "Rehabilitation progress"])
            if st.button("Log local hand-off demonstration", use_container_width=True, disabled=not bool(last_record), key="care_log_handoff"):
                st.session_state["share_log"].append(
                    {
                        "time": datetime.now().strftime("%d %b %Y, %H:%M:%S"),
                        "record": last_record.get("record_id"),
                        "recipient": recipient,
                        "purpose": purpose,
                    }
                )
                st.success("The local demonstration log was updated. No external data was transmitted.")
    with log_col:
        with st.container(border=True):
            st.markdown("#### Local hand-off log")
            logs = list(reversed(st.session_state.get("share_log", [])))
            if logs:
                st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
            else:
                empty_state("No hand-offs logged", "Demonstration activity will appear here.")

    st.markdown("### Integration roadmap")
    with st.container(border=True):
        roadmap = [
            ("Consent and identity", "Add explicit participant consent, identity matching, and role-based access controls."),
            ("Clinical validation", "Compare outputs with physiotherapist ratings and accepted gait or balance tests."),
            ("Interoperability", "Map assessment fields to an approved health-data exchange workflow before claiming FHIR support."),
            ("Security", "Add encrypted persistent storage, audit logs, data-retention controls, and organisational governance."),
        ]
        for title, description in roadmap:
            st.markdown(f"**{title}**  \n{description}")


# =============================================================================
# About
# =============================================================================

def show_about() -> None:
    page_header(
        "Product and validation overview",
        "About StrideX",
        "Understand the project positioning, technical architecture, present limitations, and the pathway from hackathon prototype to a clinically evaluated product.",
    )
    prototype_banner()

    left, right = st.columns([1.15, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("#### What StrideX does")
            st.write(
                "StrideX is an AI-assisted mobility screening and longitudinal monitoring prototype. "
                "It combines a transparent pressure/pain screening engine with optional pose-derived "
                "movement indicators from walking media. The output is an explainable screening priority, "
                "not a neurological diagnosis."
            )
            st.markdown("#### Intended users")
            st.write("Physiotherapists, rehabilitation centres, geriatric programmes, research teams, and clinicians conducting follow-up mobility review.")
            st.markdown("#### Primary use cases")
            st.write("Repeat mobility screening, rehabilitation follow-up, fall-risk workflow support, and referral prioritisation.")

        with st.container(border=True):
            st.markdown("#### Technical architecture")
            workflow_strip()

    with right:
        with st.container(border=True):
            st.markdown("#### Current limitations")
            limitations = [
                "The pressure index is normalized prototype input, not a calibrated pressure unit.",
                "Pain is self-reported; it is not detected from video.",
                "Pose estimates are affected by camera angle, lighting, clothing, obstruction, and capture distance.",
                "Demo fallback metrics are generated and always labelled as demonstration data.",
                "Screening thresholds have not been clinically validated.",
                "Session records are not persistent and disappear when the Streamlit session resets.",
                "The login system is for demonstration only and is not production-grade authentication.",
            ]
            for item in limitations:
                st.markdown(f"- {item}")

        with st.container(border=True):
            st.markdown("#### Validation roadmap")
            roadmap = [
                "Define a standard 10–20 second capture protocol.",
                "Collect consented data with representative participants.",
                "Compare measurements with clinician ratings and validated mobility tests.",
                "Evaluate reliability, sensitivity, specificity, calibration, and subgroup performance.",
                "Complete privacy, security, ethics, and regulatory review before clinical deployment.",
            ]
            for index, item in enumerate(roadmap, start=1):
                st.markdown(f"**{index}.** {item}")

    st.markdown("### Runtime capabilities")
    capabilities = get_capabilities()
    device_status = get_device_status()
    capability_rows = [
        {"Component": "MediaPipe pose runtime", "Status": "Available" if capabilities["mediapipe_available"] else "Not installed"},
        {"Component": "OpenCV video runtime", "Status": "Available" if capabilities["opencv_available"] else "Not installed"},
        {"Component": "Pose processing mode", "Status": device_status["pose_engine"]},
        {"Component": "Wearable sensor", "Status": device_status["sensor"]},
        {"Component": "Data storage", "Status": device_status["storage"]},
        {"Component": "Reporting", "Status": device_status["reporting"]},
    ]
    st.dataframe(pd.DataFrame(capability_rows), use_container_width=True, hide_index=True)

    st.markdown("### Recommended capture guidance")
    g1, g2, g3, g4 = st.columns(4)
    guidance = [
        (g1, "Full body visible", "Keep head, hips, knees, ankles, heels, and feet inside the frame."),
        (g2, "Stable camera", "Use a fixed camera position and avoid panning while the person walks."),
        (g3, "Good lighting", "Avoid backlighting, deep shadows, and low-contrast clothing."),
        (g4, "Repeatable setup", "Use similar distance, footwear, walking path, and instructions during follow-up."),
    ]
    for col, title, text in guidance:
        with col:
            st.markdown(
                f'<div class="sx-mode-card" style="min-height:145px"><div class="sx-mode-title">{escape(title)}</div><div class="sx-mode-text">{escape(text)}</div></div>',
                unsafe_allow_html=True,
            )


# =============================================================================
# Router
# =============================================================================

def main() -> None:
    if not st.session_state["logged_in"]:
        if st.session_state["auth_page"] == "signup":
            show_signup()
        else:
            show_login()
        return

    page = render_sidebar()
    if page == "Dashboard":
        show_dashboard()
    elif page == "Assessment":
        show_assessment()
    elif page == "Patient History":
        show_history()
    elif page == "Care Network":
        show_care_network()
    elif page == "About":
        show_about()


if __name__ == "__main__":
    main()
