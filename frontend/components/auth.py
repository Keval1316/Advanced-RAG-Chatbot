import streamlit as st
from frontend.services.api_client import api_client


def render_auth_screen():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-size: 2.5rem; font-weight: 700; background: linear-gradient(90deg, #3B82F6, #8B5CF6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Enterprise AI Knowledge Assistant
        </h1>
        <p style="font-size: 1.1rem; color: #94A3B8;">
            Advanced RAG Platform with Hybrid Search, Cross-Encoder Reranking, CRAG & Citations
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Create Account"])

        with tab_login:
            with st.form("login_form"):
                st.subheader("Welcome Back")
                username_or_email = st.text_input("Username or Email", placeholder="user@company.com or username")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submit_login = st.form_submit_button("Sign In", use_container_width=True)

                if submit_login:
                    if not username_or_email or not password:
                        st.error("Please enter both username/email and password.")
                    else:
                        with st.spinner("Authenticating..."):
                            res = api_client.login(username_or_email, password)
                            if res.get("success"):
                                token_data = res["data"]
                                st.session_state["token"] = token_data["access_token"]
                                st.session_state["user"] = token_data["user"]
                                st.success("Signed in successfully!")
                                st.rerun()
                            else:
                                err = res.get("error", {}).get("message", "Login failed.")
                                st.error(f"Error: {err}")

        with tab_register:
            with st.form("register_form"):
                st.subheader("New User Registration")
                email = st.text_input("Work Email", placeholder="alex@company.com")
                username = st.text_input("Username", placeholder="alex_dev")
                reg_password = st.text_input("Password", type="password", placeholder="Min 6 characters")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="••••••••")
                submit_register = st.form_submit_button("Create Account", use_container_width=True)

                if submit_register:
                    if not email or not username or not reg_password:
                        st.error("Please fill in all fields.")
                    elif len(reg_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif reg_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        with st.spinner("Creating account..."):
                            res = api_client.register(email, username, reg_password)
                            if res.get("success"):
                                st.success("Account created successfully! Please sign in.")
                            else:
                                err = res.get("error", {}).get("message", "Registration failed.")
                                st.error(f"Error: {err}")
