import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(
    page_title="StrideX | Gait Analysis",
    page_icon="🦿",
    layout="wide"
)

# =========================
# STYLE
# =========================

st.markdown("""
<style>

.stApp {
    background:#F5F7FA;
}

header {
    visibility:hidden;
}

[data-testid="stSidebar"] {
    background:white;
}

.logo {
    font-size:28px;
    font-weight:800;
    color:#163F70;
}

.logo span {
    color:#2878C8;
}

.title {
    font-size:36px;
    font-weight:800;
    color:#172033;
}

.subtitle {
    color:#718096;
}

.card {
    background:white;
    border:1px solid #E1E7EF;
    border-radius:16px;
    padding:22px;
    box-shadow:0 5px 20px rgba(30,50,80,.05);
}

.label {
    font-size:12px;
    color:#718096;
    font-weight:700;
    text-transform:uppercase;
}

.value {
    font-size:32px;
    font-weight:800;
    color:#172033;
    margin-top:10px;
}

.unit {
    color:#8995A7;
    font-size:13px;
}

.section {
    background:white;
    border:1px solid #E1E7EF;
    border-radius:16px;
    padding:25px;
    margin-top:25px;
}

</style>
""", unsafe_allow_html=True)


# =========================
# SIDEBAR
# =========================

with st.sidebar:

    st.markdown(
        '<div class="logo">Stride<span>X</span></div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    page = st.radio(
        "WORKSPACE",
        [
            "Overview",
            "Gait Metrics",
            "Joint Analysis",
            "Risk Screening",
            "Report"
        ]
    )

    st.markdown("---")

    st.caption(
        "AI-powered biomechanical screening"
    )


# =========================
# HEADER
# =========================

st.markdown(
    '<div class="title">Gait Assessment</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Video-derived biomechanical assessment'
    '</div>',
    unsafe_allow_html=True
)

st.write("")


# =========================
# UPLOAD
# =========================

uploaded = st.file_uploader(
    "Upload walking video",
    type=["mp4", "mov", "avi", "mkv"]
)

if uploaded:

    st.success(
        f"Video uploaded successfully: {uploaded.name}"
    )

    st.video(uploaded)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "VIDEO SIZE",
            f"{uploaded.size / (1024*1024):.2f} MB"
        )

    with c2:
        st.metric(
            "FORMAT",
            uploaded.name.split(".")[-1].upper()
        )

    with c3:
        st.metric(
            "STATUS",
            "READY"
        )

    st.write("")

    if st.button(
        "▶ RUN GAIT ANALYSIS",
        type="primary",
        use_container_width=True
    ):

        progress = st.progress(0)

        stages = [
            "Loading video",
            "Detecting pose landmarks",
            "Tracking body movement",
            "Calculating joint angles",
            "Calculating gait parameters",
            "Generating biomechanical report"
        ]

        for i, stage in enumerate(stages):

            st.write(stage)

            progress.progress(
                int((i + 1) / len(stages) * 100)
            )

        # ==========================================
        # LOOK FOR EXISTING BACKEND OUTPUT
        # ==========================================

        possible_files = [

            "gait_results.csv",

            "gait_data.csv",

            "outputs/gait_results.csv",

            "outputs/gait_data.csv",

            "frontend/outputs/gait_results.csv",

            "frontend/outputs/gait_data.csv",

            "backend/gait_results.csv",

            "backend/gait_data.csv"
        ]

        result_file = None

        for file in possible_files:

            if os.path.exists(file):

                result_file = file

                break


        if result_file:

            df = pd.read_csv(result_file)

            st.session_state["gait_data"] = df

            st.success(
                "Analysis completed. Real gait data loaded."
            )

        else:

            st.warning(
                "Pose processing completed, but the backend has not "
                "exported a gait-results CSV yet."
            )

            st.info(
                "Next we will connect your existing AI/physics pipeline "
                "directly to this dashboard."
            )


# =========================
# RESULTS
# =========================

if "gait_data" in st.session_state:

    df = st.session_state["gait_data"]

    st.markdown("---")

    st.markdown(
        "## Biomechanical Measurements"
    )


    # ==========================================
    # FIND COLUMNS
    # ==========================================

    def find_column(keywords):

        for keyword in keywords:

            for column in df.columns:

                if keyword.lower() in column.lower():

                    return column

        return None


    cadence_col = find_column([
        "cadence"
    ])

    knee_col = find_column([
        "knee_angle",
        "knee angle"
    ])

    ankle_col = find_column([
        "ankle_angle",
        "ankle angle"
    ])

    velocity_col = find_column([
        "angular_velocity",
        "angular velocity"
    ])

    sway_col = find_column([
        "postural_sway",
        "postural sway",
        "sway"
    ])

    asymmetry_col = find_column([
        "asymmetry",
        "step_asymmetry"
    ])


    def get_mean(column):

        if column is None:

            return None

        values = pd.to_numeric(
            df[column],
            errors="coerce"
        ).dropna()

        if len(values) == 0:

            return None

        return values.mean()


    cadence = get_mean(cadence_col)

    knee = get_mean(knee_col)

    ankle = get_mean(ankle_col)

    velocity = get_mean(velocity_col)

    sway = get_mean(sway_col)

    asymmetry = get_mean(asymmetry_col)


    # ==========================================
    # METRIC CARD
    # ==========================================

    def metric_card(
        column,
        label,
        value,
        unit
    ):

        with column:

            if value is None:

                value_text = "—"

            else:

                value_text = f"{value:.2f}"

            st.markdown(
                f"""
                <div class="card">

                <div class="label">
                {label}
                </div>

                <div class="value">
                {value_text}
                </div>

                <div class="unit">
                {unit}
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )


    c1, c2, c3 = st.columns(3)

    metric_card(
        c1,
        "Cadence",
        cadence,
        "steps / minute"
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
        velocity,
        "degrees / second"
    )

    metric_card(
        c2,
        "Postural Sway",
        sway,
        "normalized"
    )

    metric_card(
        c3,
        "Step Asymmetry",
        asymmetry,
        "index"
    )


    # ==========================================
    # GAIT GRAPH
    # ==========================================

    if page in ["Overview", "Gait Metrics"]:

        st.markdown(
            '<div class="section">',
            unsafe_allow_html=True
        )

        st.subheader(
            "Gait Measurement Trends"
        )

        numeric_columns = df.select_dtypes(
            include=np.number
        ).columns.tolist()

        if numeric_columns:

            selected = st.multiselect(
                "Select measurements to visualize",
                numeric_columns,
                default=numeric_columns[:min(3, len(numeric_columns))]
            )

            if selected:

                st.line_chart(
                    df[selected],
                    height=420
                )

        else:

            st.info(
                "No numeric measurements were found."
            )

        st.markdown("</div>", unsafe_allow_html=True)


    # ==========================================
    # JOINT ANALYSIS
    # ==========================================

    if page in ["Overview", "Joint Analysis"]:

        st.markdown(
            '<div class="section">',
            unsafe_allow_html=True
        )

        st.subheader(
            "Joint Angle Analysis"
        )

        joint_columns = []

        for column in df.columns:

            name = column.lower()

            if (
                "knee" in name
                or "ankle" in name
                or "hip" in name
            ):

                if pd.api.types.is_numeric_dtype(
                    df[column]
                ):

                    joint_columns.append(column)


        if joint_columns:

            st.line_chart(
                df[joint_columns],
                height=420
            )

        else:

            st.info(
                "Joint-angle measurements will appear here "
                "when exported by the analysis engine."
            )

        st.markdown("</div>", unsafe_allow_html=True)


    # ==========================================
    # RISK
    # ==========================================

    if page in ["Overview", "Risk Screening"]:

        st.markdown(
            '<div class="section">',
            unsafe_allow_html=True
        )

        st.subheader(
            "Risk Screening"
        )

        st.warning(
            "Screening indicators are not medical diagnoses."
        )

        if asymmetry is None:

            st.info(
                "Insufficient asymmetry data for screening."
            )

        else:

            if abs(asymmetry) < 0.05:

                st.success(
                    "LOW — No significant asymmetry signal detected."
                )

            elif abs(asymmetry) < 0.10:

                st.warning(
                    "MODERATE — Asymmetry signal detected."
                )

            else:

                st.error(
                    "ELEVATED — Significant asymmetry signal detected."
                )

        st.markdown("</div>", unsafe_allow_html=True)


    # ==========================================
    # RAW DATA
    # ==========================================

    if page in ["Overview", "Gait Metrics", "Report"]:

        st.markdown(
            '<div class="section">',
            unsafe_allow_html=True
        )

        st.subheader(
            "Frame-Level Measurements"
        )

        st.dataframe(
            df,
            use_container_width=True,
            height=400
        )

        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Gait Dataset",
            csv,
            "StrideX_Gait_Data.csv",
            "text/csv"
        )

        st.markdown("</div>", unsafe_allow_html=True)


# =========================
# FOOTER
# =========================

st.markdown("---")

st.caption(
    "StrideX | Video-derived biomechanical screening research prototype"
)