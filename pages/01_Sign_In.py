import streamlit as st

st.set_page_config(
    page_title="StrideX — Sign In",
    page_icon="🦿",
    layout="centered"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background: #F5F8FC;
}

header {
    visibility: hidden;
}

.block-container {
    max-width: 520px;
    padding-top: 70px;
}

.logo {
    text-align: center;
    font-size: 38px;
    font-weight: 800;
    color: #163F70;
    letter-spacing: -1px;
}

.logo span {
    color: #2878C8;
}

.tagline {
    text-align: center;
    color: #718096;
    font-size: 15px;
    margin-top: 8px;
    margin-bottom: 40px;
}

.login-card {
    background: white;
    border: 1px solid #E1E7EF;
    border-radius: 22px;
    padding: 35px;
    box-shadow: 0 15px 45px rgba(30,60,90,0.08);
}

.login-title {
    font-size: 28px;
    font-weight: 750;
    color: #172033;
    margin-bottom: 5px;
}

.login-subtitle {
    color: #718096;
    margin-bottom: 25px;
}

.security {
    background: #F3F8FD;
    border: 1px solid #DCEAF7;
    border-radius: 12px;
    padding: 14px;
    color: #52677D;
    font-size: 13px;
    margin-top: 20px;
}

.footer {
    text-align: center;
    color: #8995A7;
    font-size: 12px;
    margin-top: 30px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOGO
# ============================================================

st.markdown("""
<div class="logo">
    Stride<span>X</span>
</div>

<div class="tagline">
    AI-Powered Biomechanical Gait Screening
</div>
""", unsafe_allow_html=True)


# ============================================================
# LOGIN CARD
# ============================================================

st.markdown("""
<div class="login-card">

<div class="login-title">
    Welcome back
</div>

<div class="login-subtitle">
    Sign in to access your gait analysis workspace.
</div>

</div>
""", unsafe_allow_html=True)


# ============================================================
# LOGIN FORM
# ============================================================

email = st.text_input(
    "Email address",
    placeholder="clinician@example.com"
)

password = st.text_input(
    "Password",
    type="password",
    placeholder="Enter your password"
)

remember = st.checkbox(
    "Remember me"
)

st.write("")


# ============================================================
# SIGN IN
# ============================================================

if st.button(
    "SIGN IN",
    type="primary",
    use_container_width=True
):

    if email.strip() and password.strip():

        st.session_state["logged_in"] = True
        st.session_state["user_email"] = email

        st.success("Sign in successful.")

        # CORRECT STREAMLIT PAGE
        st.switch_page(
            "pages/02_Gait_Analysis.py"
        )

    else:

        st.error(
            "Please enter your email address and password."
        )


# ============================================================
# SECURITY MESSAGE
# ============================================================

st.markdown("""
<div class="security">
    🔒 <b>Secure research workspace</b><br>
    Your gait assessment data is processed for biomechanical
    screening and monitoring.
</div>
""", unsafe_allow_html=True)


# ============================================================
# CREATE ACCOUNT
# ============================================================

st.markdown(
    "<br><div style='text-align:center;color:#718096;'>"
    "New to StrideX?"
    "</div>",
    unsafe_allow_html=True
)

if st.button(
    "Create an account",
    use_container_width=True
):

    st.info(
        "Account registration will be connected to "
        "authentication in the next integration step."
    )


# ============================================================
# BACK TO LANDING
# ============================================================

if st.button(
    "← Back to StrideX",
    use_container_width=True
):

    st.switch_page("app.py")


# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">
    StrideX Research Prototype<br><br>
    Screening and monitoring only — not a medical diagnosis.
</div>
""", unsafe_allow_html=True)