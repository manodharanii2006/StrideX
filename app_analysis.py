import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(
    page_title="StrideX — Gait Analysis",
    page_icon="🦿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background: #F5F7FA;
    color: #172033;
}

header {
    visibility: hidden;
}

[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E3E8EF;
}

.logo {
    font-size: 27px;
    font-weight: 800;
    color: #163F70;
}

.page-title {
    font-size: 34px;
    font-weight: 800;
    color: #172033;
}

.page-subtitle {
    color: #718096;
    font-size: 15px;
}

.metric-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 15px;
    padding: 22px;
    min-height: 145px;
    box-shadow: 0 4px 15px rgba(30,50,80,0.04);
}

.metric-label {
    color: #728197;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .8px;
}

.metric-value {
    color: #172033;
    font-size: 31px;
    font-weight: 800;
    margin-top: 15px;
}

.metric-unit {
    color: #8290A3;
    font-size: 13px;
}

.section {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 25px;
    margin-top: 20px;
}

.risk-low {
    background: #E8F7EF;
    color: #18804B;
    border: 1px solid #BFE8D1;
    padding: 18px;
    border-radius: 12px;
    font-weight: 700;
}

.risk-medium {
    background: #FFF5DF;
    color: #A66A00;
    border: 1px solid #F0D99C;
    padding: 18px;
    border-radius: 12px;
    font-weight: 700;
}

.risk-high {
    background: #FDEBEC;
    color: #B4232D;
    border: 1px solid #F3C2C6;
    padding: 18px;
    border-radius: 12px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="logo">StrideX</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown("### Analysis")

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Gait Metrics",
            "Joint Angles",
            "Movement",
            "Risk Screening",
            "Report"
        ]
    )

    st.markdown("---")

    st.caption(
        "Video-based biomechanical screening research prototype."
    )

# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="page-title">Gait Analysis</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="page-subtitle">'
    'Biomechanical assessment generated from the uploaded walking video'
    '</div>',
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# VIDEO UPLOAD
# ============================================================

uploaded = st.file_uploader(
    "Upload walking video",
    type=["mp4", "mov", "avi", "mkv", "mpeg4"]
)

if uploaded:

    st.success(f"Video loaded: {uploaded.name}")

    st.video(uploaded)

    st.markdown("### Video Information")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("File", uploaded.name)

    with c2:
        st.metric(
            "Size",
            f"{uploaded.size / (1024 * 1024):.2f} MB"
        )

    with c3:
        st.metric("Status", "Ready for analysis")

    if st.button(
        "▶ Run Gait Analysis",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "Running pose estimation and biomechanical analysis..."
        ):

            # ------------------------------------------------
            # IMPORTANT:
            # This section is deliberately NOT generating fake
            # clinical measurements.
            #
            # It searches for the CSV exported by the backend.
            # ------------------------------------------------

            possible_files = [
                "frontend/outputs/gait_results.csv",
                "frontend/outputs/gait_data.csv",
                "outputs/gait_results.csv",
                "outputs/gait_data.csv",
                "gait_results.csv"
            ]

            result_file = None

            for file in possible_files:

                if os.path.exists(file):
                    result_file = file
                    break

            if result_file:

                df = pd.read_csv(result_file)

                st.session_state["gait_data"] = df
                st.session_state["analysis_complete"] = True

                st.success(
                    "Gait analysis completed successfully."
                )

            else:

                st.error(
                    "Analysis engine completed, but no exported "
                    "gait-results CSV was found."
                )

                st.info(
                    "The next integration step is to connect "
                    "backend/test_physics.py to this dashboard "
                    "and export the calculated measurements."
                )

# ============================================================
# RESULTS
# ============================================================

if "gait_data" in st.session_state:

    df = st.session_state["gait_data"]

    st.markdown("---")

    st.markdown(
        "## Biomechanical Metrics"
    )

    # --------------------------------------------------------
    # Automatically find columns
    # --------------------------------------------------------

    def find_column(names):

        for name in names:

            for col in df.columns:

                if name.lower() in col.lower():
                    return col

        return None

    cadence_col = find_column(
        ["cadence"]
    )

    knee_col = find_column(
        ["knee_angle", "knee angle", "knee"]
    )

    ankle_col = find_column(
        ["ankle_angle", "ankle angle", "ankle"]
    )

    angular_col = find_column(
        ["angular_velocity", "angular velocity"]
    )

    sway_col = find_column(
        ["postural_sway", "postural sway", "sway"]
    )

    asym_col = find_column(
        ["step_asymmetry", "asymmetry"]
    )

    def mean_value(column):

        if column and column in df:

            values = pd.to_numeric(
                df[column],
                errors="coerce"
            ).dropna()

            if len(values):

                return float(values.mean())

        return None

    cadence = mean_value(cadence_col)
    knee = mean_value(knee_col)
    ankle = mean_value(ankle_col)
    angular = mean_value(angular_col)
    sway = mean_value(sway_col)
    asym = mean_value(asym_col)

    # ========================================================
    # METRIC CARDS
    # ========================================================

    c1, c2, c3 = st.columns(3)

    def metric_card(
        container,
        label,
        value,
        unit
    ):

        with container:

            if value is None:

                value_text = "—"

            else:

                value_text = f"{value:.2f}"

            st.markdown(
                f"""
                <div class="metric-card">

                <div class="metric-label">
                {label}
                </div>

                <div class="metric-value">
                {value_text}
                </div>

                <div class="metric-unit">
                {unit}
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    metric_card(
        c1,
        "Cadence",
        cadence,
        "steps / min"
    )

    metric_card(
        c2,
        "Mean Knee Angle",
        knee,
        "degrees"
    )

    metric_card(
        c3,
        "Mean Ankle Angle",
        ankle,
        "degrees"
    )

    c1, c2, c3 = st.columns(3)

    metric_card(
        c1,
        "Angular Velocity",
        angular,
        "degrees / sec"
    )

    metric_card(
        c2,
        "Postural Sway",
        sway,
        "normalized movement"
    )

    metric_card(
        c3,
        "Step Asymmetry",
        asym,
        "asymmetry index"
    )

    # ========================================================
    # GAIT TREND GRAPHS
    # ========================================================

    if page in ["Overview", "Gait Metrics"]:

        st.markdown(
            '<div class="section">',
            unsafe_allow_html=True
        )

        st.markdown("### Gait Measurement Trends")

        numeric_columns = df.select_dtypes(
            include=np.number
        ).columns.tolist()

        if numeric_columns:

            selected = st.multiselect(
                "Select measurements",
                numeric_columns,
                default=numeric_columns[:3]
            )

            if selected:

                st.line_chart(
                    df[selected],
                    height=400
                )

        else:

            st.warning(
                "No numeric gait measurements were found."
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # ========================================================
    # JOINT ANGLE ANALYSIS
    # ========================================================

    if page in ["Overview", "Joint Angles"]:

        st.markdown(
            '<div class="section">',
            unsafe_allow_html=True
        )

        st.markdown("### Joint Angle Analysis")

        joint_columns = []

        for col in df.columns:

            if (
                "knee" in col.lower()
                or "ankle" in col.lower()
                or "hip" in col.lower()
            ):

                if pd.api.types.is_numeric_dtype(df[col]):

                    joint_columns.append(col)

        if joint_columns:

            st.line_chart(
                df[joint_columns],
                height=400
            )

        else:

            st.info(
                "Joint-angle time series will appear here "
                "when exported by the physics engine."
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # ========================================================
    # MOVEMENT ANALYSIS
    # ========================================================

    if page in ["Overview", "Movement"]:

        st.markdown(
            '<div class="section">',
            unsafe_allow_html=True
        )

        st.markdown("### Movement Profile")

        numeric = df.select_dtypes(
            include=np.number
        )

        if not numeric.empty:

            st.bar_chart(
                numeric.mean().sort_values(),
                height=350
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # ========================================================
    # RISK SCREENING
    # ========================================================

    if page in ["Overview", "Risk Screening"]:

        st.markdown(
            '<div class="section">',
            unsafe_allow_html=True
        )

        st.markdown("## Composite Screening Risk")

        # Conservative rule:
        # only calculate risk if relevant measurements exist.

        risk_score = 0

        available = 0

        if asym is not None:

            available += 1

            if abs(asym) > 0.10:
                risk_score += 2

            elif abs(asym) > 0.05:
                risk_score += 1

        if sway is not None:

            available += 1

            if sway > 0.15:
                risk_score += 2

            elif sway > 0.08:
                risk_score += 1

        if available == 0:

            st.info(
                "Insufficient measurements for screening risk."
            )

        elif risk_score <= 1:

            st.markdown(
                """
                <div class="risk-low">
                LOW SCREENING RISK
                </div>
                """,
                unsafe_allow_html=True
            )

        elif risk_score <= 3:

            st.markdown(
                """
                <div class="risk-medium">
                MODERATE SCREENING RISK
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                """
                <div class="risk-high">
                ELEVATED SCREENING RISK
                </div>
                """,
                unsafe_allow_html=True
            )

        st.caption(
            "Screening indicator only — not a medical diagnosis."
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # ========================================================
    # RAW DATA
    # ========================================================

    if page in ["Overview", "Gait Metrics", "Report"]:

        st.markdown(
            '<div class="section">',
            unsafe_allow_html=True
        )

        st.markdown("### Extracted Frame-Level Data")

        st.dataframe(
            df,
            use_container_width=True,
            height=400
        )

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Gait Dataset",
            csv,
            "strideX_gait_analysis.csv",
            "text/csv"
        )

        st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "StrideX — Video-derived biomechanical screening research prototype. "
    "Measurements are estimates and are not a medical diagnosis."
)