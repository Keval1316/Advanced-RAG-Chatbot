import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Enterprise AI Knowledge Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich modern aesthetics
st.markdown("""
<style>
    /* Dark Theme & Modern Glassmorphism Aesthetic */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(15, 23, 42) 0%, rgb(10, 15, 29) 90%);
        color: #F8FAFC;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Modern Card Styles */
    .metric-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.2rem;
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
    }
    
    /* Smooth Badges */
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-ready { background: rgba(34, 197, 94, 0.2); color: #4ADE80; border: 1px solid rgba(34, 197, 94, 0.4); }
    .badge-processing { background: rgba(234, 179, 8, 0.2); color: #FACC15; border: 1px solid rgba(234, 179, 8, 0.4); }
    .badge-failed { background: rgba(239, 68, 68, 0.2); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.4); }

    /* Button Polish */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

from frontend.services.api_client import api_client
from frontend.components.auth import render_auth_screen
from frontend.components.sidebar import render_sidebar
from frontend.components.citations import render_citations

# Initialize session state keys
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None
if "active_kb_id" not in st.session_state:
    st.session_state["active_kb_id"] = None
if "active_conv_id" not in st.session_state:
    st.session_state["active_conv_id"] = None
if "nav" not in st.session_state:
    st.session_state["nav"] = "chat"


def render_chat_view():
    token = st.session_state["token"]
    kb_id = st.session_state.get("active_kb_id")

    if not kb_id:
        st.warning("⚠️ No active Knowledge Base selected. Please select or create one in the sidebar to start chatting.")
        return

    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <h2 style="margin-bottom: 0.2rem; font-weight: 700;">💬 Multi-Turn Knowledge Chat</h2>
        <p style="color: #94A3B8; font-size: 0.95rem;">Ask questions grounded in your uploaded documents. Powered by Groq & Hybrid RAG.</p>
    </div>
    """, unsafe_allow_html=True)

    conv_id = st.session_state.get("active_conv_id")

    # Load messages
    messages = []
    if conv_id:
        res = api_client.get_messages(token, conv_id)
        if res.get("success"):
            messages = res.get("data", [])

    # Render message history
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        citations = m.get("citations", [])
        metadata = m.get("msg_metadata", {}) or m.get("metadata", {})

        with st.chat_message(role):
            st.markdown(content)
            if role == "assistant":
                render_citations(citations, metadata)

    # Chat input
    if prompt := st.chat_input("Ask a question about your knowledge base..."):
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving sources and synthesizing grounded answer..."):
                res = api_client.send_message(
                    token=token,
                    kb_id=kb_id,
                    message=prompt,
                    conv_id=conv_id
                )

                if res.get("success"):
                    data = res["data"]
                    answer = data.get("answer", "")
                    citations = data.get("citations", [])
                    metadata = data.get("metadata", {})
                    st.session_state["active_conv_id"] = data.get("conversation_id")

                    st.markdown(answer)
                    render_citations(citations, metadata)
                    st.rerun()
                else:
                    err = res.get("error", {}).get("message", "Error processing request.")
                    st.error(f"Failed to generate answer: {err}")


def render_knowledge_bases_view():
    token = st.session_state["token"]
    st.markdown("## 📚 Knowledge Base Management")
    st.markdown("Create and manage isolated document repositories with dedicated vector and metadata scopes.")

    with st.expander("➕ Create New Knowledge Base", expanded=False):
        with st.form("create_kb_form"):
            kb_name = st.text_input("Knowledge Base Name", placeholder="e.g. Q1 Financial Reports or Engineering Manuals")
            kb_desc = st.text_area("Description (Optional)", placeholder="Describe the scope and contents of this knowledge base.")
            submit = st.form_submit_button("Create Knowledge Base")

            if submit:
                if not kb_name:
                    st.error("Please provide a name for the knowledge base.")
                else:
                    with st.spinner("Creating knowledge base..."):
                        res = api_client.create_knowledge_base(token, kb_name, kb_desc)
                        if res.get("success"):
                            st.success(f"Knowledge Base '{kb_name}' created successfully!")
                            st.session_state["active_kb_id"] = res["data"]["id"]
                            st.rerun()
                        else:
                            st.error(res.get("error", {}).get("message", "Failed to create knowledge base."))

    st.markdown("### Existing Knowledge Bases")
    kb_res = api_client.list_knowledge_bases(token)
    kbs = kb_res.get("data", []) if kb_res.get("success") else []

    if not kbs:
        st.info("No knowledge bases created yet. Use the form above to create your first one.")
    else:
        for kb in kbs:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"**{kb['name']}**")
                if kb.get("description"):
                    st.markdown(f"<span style='color: #94A3B8; font-size: 0.85rem;'>{kb['description']}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"📄 {kb.get('document_count', 0)} Docs")
            with col3:
                st.markdown(f"💬 {kb.get('conversation_count', 0)} Chats")
            with col4:
                if st.button("🗑️ Delete", key=f"del_kb_{kb['id']}"):
                    api_client.delete_knowledge_base(token, kb["id"])
                    if st.session_state.get("active_kb_id") == kb["id"]:
                        st.session_state["active_kb_id"] = None
                    st.success("Deleted!")
                    st.rerun()
            st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.15;'>", unsafe_allow_html=True)


def render_documents_view():
    token = st.session_state["token"]
    kb_id = st.session_state.get("active_kb_id")

    st.markdown("## 📄 Document Ingestion Manager")
    if not kb_id:
        st.warning("⚠️ Please select an active Knowledge Base in the sidebar to view and upload documents.")
        return

    st.markdown("Upload documents (**PDF, DOCX, TXT**) to automatically extract text, create recursive chunks, generate dense & sparse embeddings, and index into Qdrant.")

    with st.expander("📤 Upload Document", expanded=True):
        uploaded_file = st.file_uploader(
            "Choose a file to upload",
            type=["pdf", "docx", "txt", "md"],
            help="Files are validated, chunked (800 chars), and embedded into the active knowledge base."
        )
        if uploaded_file is not None:
            if st.button("🚀 Process & Ingest Document", use_container_width=True):
                with st.spinner("Extracting text, chunking, and indexing into Qdrant vector database..."):
                    file_bytes = uploaded_file.read()
                    res = api_client.upload_document(
                        token=token,
                        kb_id=kb_id,
                        file_bytes=file_bytes,
                        filename=uploaded_file.name,
                        content_type=uploaded_file.type or "application/octet-stream"
                    )
                    if res.get("success"):
                        doc_data = res.get("data", {})
                        st.success(f"✅ Ingested '{uploaded_file.name}' into {doc_data.get('chunk_count', 0)} chunks!")
                        st.rerun()
                    else:
                        st.error(res.get("error", {}).get("message", "Upload failed."))

    st.markdown("### Uploaded Documents in Current Knowledge Base")
    doc_res = api_client.list_documents(token, kb_id)
    docs = doc_res.get("data", []) if doc_res.get("success") else []

    if not docs:
        st.info("No documents uploaded to this knowledge base yet.")
    else:
        for doc in docs:
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            with col1:
                st.markdown(f"📄 **{doc['original_filename']}**")
            with col2:
                status = doc.get("status", "ready")
                badge_class = f"badge-{status}"
                st.markdown(f"<span class='status-badge {badge_class}'>{status.upper()}</span>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"{doc.get('chunk_count', 0)} Chunks")
            with col4:
                size_kb = round(doc.get('file_size', 0) / 1024, 1)
                st.markdown(f"{size_kb} KB")
            with col5:
                if st.button("🗑️", key=f"del_doc_{doc['id']}"):
                    api_client.delete_document(token, doc["id"])
                    st.success("Document deleted!")
                    st.rerun()
            st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.15;'>", unsafe_allow_html=True)


def main():
    if not st.session_state.get("token"):
        render_auth_screen()
    else:
        render_sidebar()
        nav = st.session_state.get("nav", "chat")
        if nav == "chat":
            render_chat_view()
        elif nav == "kbs":
            render_knowledge_bases_view()
        elif nav == "docs":
            render_documents_view()


if __name__ == "__main__":
    main()
