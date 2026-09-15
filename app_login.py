import streamlit as st

st.set_page_config(
    page_title="StrideX — Sign In",
    page_icon="🦿",
    layout="centered"
)

st.markdown("""
<style>

.stApp {
    background: #F7F9FC;
}

header {
    visibility: hidden;
}

.login-container {
    background: white;
    border: 1px solid #E3E9F1;
    border-radius: 20px;
    padding: 45px;
    box-shadow: 0 15px 45px rgba(30,60,90,0.08);
}

.logo {
    font-size: 30px;
    font-weight: 800;
    color: #163F70;
    text-align: center;
}

.subtitle {
    text-align: center;
    color: #718096;
    margin-top: 8px;
    margin-bottom: 35px;
}

.small {
    text-align: center;
    color: #8A96A8;
    font-size: 13px;
    margin-top: 25px;
}

</style>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

st.markdown("""
<div class="login-container">

<div class="logo">StrideX</div>

<div class="subtitle">
Biomechanical Gait Screening Platform
</div>

</div>
""", unsafe_allow_html=True)

st.markdown("### Sign in")

email = st.text_input(
    "Email address",
    placeholder="name@example.com"
)

password = st.text_input(
    "Password",
    type="password",
    placeholder="Enter your password"
)

remember = st.checkbox("Remember me")

if st.button("Sign In", use_container_width=True):

    if email and password:

        st.session_state["logged_in"] = True
        st.session_state["user_email"] = email

        st.success("Sign in successful.")

        st.switch_page("app_analysis.py")

    else:
        st.error("Please enter your email and password.")

st.markdown("---")

st.markdown(
    "<div class='small'>New to StrideX?</div>",
    unsafe_allow_html=True
)

if st.button("Create an account", use_container_width=True):

    st.info(
        "Account registration can be connected to Firebase authentication "
        "in the next integration step."
    )

if st.button("← Back to StrideX", use_container_width=True):
    st.switch_page("app.py")