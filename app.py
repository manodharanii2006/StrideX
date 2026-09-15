import streamlit as st

st.set_page_config(
    page_title="StrideX",
    page_icon="🦿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------- CSS ----------
st.markdown("""
<style>

.stApp {
    background: #F7F9FC;
    color: #172033;
}

.block-container {
    max-width: 1250px;
    padding-top: 0rem;
}

header {
    visibility: hidden;
}

.navbar {
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #E5EAF1;
    background: white;
    padding: 0 30px;
}

.logo {
    font-size: 27px;
    font-weight: 800;
    color: #163F70;
}

.navtext {
    color: #65738B;
    font-size: 15px;
}

.hero {
    padding: 90px 20px 70px 20px;
}

.eyebrow {
    color: #2878C8;
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 1.5px;
}

.hero-title {
    font-size: 58px;
    line-height: 1.05;
    font-weight: 800;
    color: #152238;
    margin-top: 15px;
}

.hero-title span {
    color: #2878C8;
}

.hero-text {
    font-size: 19px;
    line-height: 1.7;
    color: #68768B;
    max-width: 680px;
    margin-top: 25px;
}

.card {
    background: white;
    border: 1px solid #E3E9F1;
    border-radius: 18px;
    padding: 28px;
    height: 100%;
    box-shadow: 0 6px 25px rgba(25,55,90,0.05);
}

.card-icon {
    font-size: 32px;
}

.card-title {
    font-size: 20px;
    font-weight: 700;
    margin-top: 15px;
    color: #1C2B40;
}

.card-text {
    color: #718096;
    line-height: 1.6;
    margin-top: 10px;
}

.section-title {
    font-size: 34px;
    font-weight: 750;
    color: #172033;
    margin-bottom: 30px;
}

.disclaimer {
    background: #EEF5FC;
    border: 1px solid #D7E7F7;
    padding: 18px 22px;
    border-radius: 12px;
    color: #52657A;
    margin-top: 50px;
}

</style>
""", unsafe_allow_html=True)

# ---------- NAVBAR ----------
st.markdown("""
<div class="navbar">
    <div class="logo">StrideX</div>
    <div class="navtext">
        AI-Powered Biomechanical Gait Screening
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- HERO ----------
st.markdown("""
<div class="hero">

<div class="eyebrow">
AI-POWERED BIOMECHANICAL SCREENING
</div>

<div class="hero-title">
Understand movement.<br>
<span>Measure gait.</span>
</div>

<div class="hero-text">
StrideX transforms an ordinary walking video into quantitative
biomechanical measurements using computer vision, pose estimation
and gait analysis algorithms.
</div>

</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Start Gait Assessment  →", use_container_width=True):
        st.switch_page("app_login.py")

with col2:
    if st.button("View Analysis Dashboard", use_container_width=True):
        st.switch_page("app_analysis.py")

st.markdown("<br><br>", unsafe_allow_html=True)

# ---------- FEATURES ----------
st.markdown(
    '<div class="section-title">From video to measurable biomechanics</div>',
    unsafe_allow_html=True
)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="card">
        <div class="card-icon">🎥</div>
        <div class="card-title">Video-Based Capture</div>
        <div class="card-text">
        Upload a walking video without requiring a laboratory
        motion-capture system.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="card">
        <div class="card-icon">🧠</div>
        <div class="card-title">Pose & Gait Intelligence</div>
        <div class="card-text">
        Extract body landmarks and derive temporal and
        biomechanical gait features.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="card">
        <div class="card-icon">📊</div>
        <div class="card-title">Clinical-Style Reporting</div>
        <div class="card-text">
        Convert movement data into interpretable metrics,
        trends, graphs and screening indicators.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer">
<b>Research prototype:</b> StrideX provides video-derived biomechanical
screening measurements. It is not intended to diagnose medical conditions.
</div>
""", unsafe_allow_html=True)