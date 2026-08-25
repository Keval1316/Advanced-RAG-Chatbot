import streamlit as st
from frontend.services.api_client import api_client


def render_sidebar():
    token = st.session_state.get("token")
    user = st.session_state.get("user", {})

    with st.sidebar:
        # User Header
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.7); padding: 0.8rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 0.85rem; color: #94A3B8;">Signed in as</div>
            <div style="font-size: 1.05rem; font-weight: 600; color: #F8FAFC;">👤 {user.get('username', 'User')}</div>
            <div style="font-size: 0.8rem; color: #64748B;">{user.get('email', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.markdown("---")

        # Navigation
        current_nav = st.radio(
            "Navigation",
            ["💬 Chat", "📚 Knowledge Bases", "📄 Document Manager"],
            index=0 if st.session_state.get("nav") == "chat" else 1 if st.session_state.get("nav") == "kbs" else 2,
            label_visibility="collapsed"
        )
        if current_nav == "💬 Chat":
            st.session_state["nav"] = "chat"
        elif current_nav == "📚 Knowledge Bases":
            st.session_state["nav"] = "kbs"
        else:
            st.session_state["nav"] = "docs"

        st.markdown("---")

        # Knowledge Base Selector
        st.subheader("📚 Active Knowledge Base")
        kb_res = api_client.list_knowledge_bases(token)
        kbs = kb_res.get("data", []) if kb_res.get("success") else []

        if not kbs:
            st.info("No knowledge bases found. Please create one to get started.")
            st.session_state["active_kb_id"] = None
        else:
            kb_options = {kb["name"]: kb["id"] for kb in kbs}
            active_name = None
            if st.session_state.get("active_kb_id"):
                for name, k_id in kb_options.items():
                    if k_id == st.session_state["active_kb_id"]:
                        active_name = name
                        break

            selected_name = st.selectbox(
                "Select Knowledge Base",
                options=list(kb_options.keys()),
                index=list(kb_options.keys()).index(active_name) if active_name in kb_options else 0,
                label_visibility="collapsed"
            )
            st.session_state["active_kb_id"] = kb_options[selected_name]

        # Conversations list (Only shown on Chat view)
        if st.session_state.get("nav") == "chat" and st.session_state.get("active_kb_id"):
            st.markdown("---")
            st.subheader("💬 Conversations")

            if st.button("➕ New Chat", use_container_width=True):
                st.session_state["active_conv_id"] = None
                st.rerun()

            convs_res = api_client.list_conversations(token, kb_id=st.session_state["active_kb_id"])
            convs = convs_res.get("data", []) if convs_res.get("success") else []

            for c in convs:
                col1, col2 = st.columns([5, 1])
                is_active = (c["id"] == st.session_state.get("active_conv_id"))
                label = f"{'👉 ' if is_active else ''}{c['title'][:22]}"
                with col1:
                    if st.button(label, key=f"conv_btn_{c['id']}", use_container_width=True):
                        st.session_state["active_conv_id"] = c["id"]
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_conv_{c['id']}"):
                        api_client.delete_conversation(token, c["id"])
                        if st.session_state.get("active_conv_id") == c["id"]:
                            st.session_state["active_conv_id"] = None
                        st.rerun()
