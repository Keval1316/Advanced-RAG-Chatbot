"""
==============================================================================
NEXUS AI — Enterprise Advanced RAG Knowledge Assistant
Hugging Face Spaces Native Gradio Application
==============================================================================
Features:
- Multi-Stage Advanced RAG: Router -> Hybrid Search (BM25 + BGE) -> RRF -> Cross-Encoder -> CRAG -> Grounded Groq LPU
- Multi-Format Document Ingestion: PDF, DOCX, TXT, MD, CSV with semantic chunking
- Grounded Source Citations with verifiable snippets & page numbers
- Multi-tenant session isolation & dynamic Groq API Key support
==============================================================================
"""

import os
import sys
import uuid
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import gradio as gr
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.db.session import engine
from backend.app.models import Base
from backend.app.rag.embeddings import embedding_service
from backend.app.rag.reranker import reranker
from backend.app.rag.parser import document_parser
from backend.app.rag.chunker import chunker
from backend.app.rag.hybrid_search import hybrid_search_service
from backend.app.rag.pipeline import rag_pipeline
from backend.app.services.vector_service import vector_service
from backend.app.rag.generator import answer_generator
from backend.app.schemas.document import ChunkMetadata

# Initialize logging and database schema
setup_logging()
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized.")
except Exception as e:
    logger.warning(f"Database schema notice: {str(e)}")

# Warm up models
try:
    embedding_service.warmup()
    reranker.warmup()
    vector_service.get_client()
    logger.info("RAG vector & reranker pipelines warmed up.")
except Exception as e:
    logger.warning(f"Warmup notice: {str(e)}")

# Session storage for in-memory session tracking
SESSION_DATA: Dict[str, Dict[str, Any]] = {}

def get_or_create_session(session_id: str) -> Dict[str, Any]:
    if not session_id or session_id not in SESSION_DATA:
        new_id = session_id or str(uuid.uuid4())
        SESSION_DATA[new_id] = {
            "user_id": uuid.uuid4(),
            "kb_id": uuid.uuid4(),
            "conversation_id": uuid.uuid4(),
            "documents": [],
            "messages": []
        }
        return SESSION_DATA[new_id]
    return SESSION_DATA[session_id]

# --- Core RAG Logic ---

def process_uploaded_files(files, session_state: str) -> Tuple[str, List[List[str]], str]:
    if not files:
        return "⚠️ No files selected.", [], session_state

    sess = get_or_create_session(session_state)
    user_id = sess["user_id"]
    kb_id = sess["kb_id"]

    status_messages = []
    for file_obj in files:
        file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
        file_name = os.path.basename(file_path)

        try:
            # Parse document
            parsed_doc = document_parser.parse_file(file_path, file_name)
            
            # Chunk document
            doc_id = uuid.uuid4()
            chunks = chunker.chunk_document(
                text=parsed_doc.content,
                filename=file_name,
                document_id=doc_id,
                user_id=user_id,
                knowledge_base_id=kb_id,
                page_count=parsed_doc.page_count
            )

            # Index into Qdrant Vector Store
            vector_service.upsert_chunks(chunks)

            # Index into BM25 Sparse Index
            hybrid_search_service.index_document_chunks(
                user_id=user_id,
                kb_id=kb_id,
                chunks=chunks
            )

            file_size_kb = round(os.path.getsize(file_path) / 1024, 1)
            sess["documents"].append({
                "name": file_name,
                "pages": parsed_doc.page_count,
                "chunks": len(chunks),
                "size": f"{file_size_kb} KB",
                "status": "Indexed"
            })
            status_messages.append(f"✅ '{file_name}': {parsed_doc.page_count} pages, {len(chunks)} chunks indexed.")
        except Exception as e:
            logger.error(f"Error processing file {file_name}: {str(e)}")
            status_messages.append(f"❌ Failed to parse '{file_name}': {str(e)}")

    doc_table = [
        [d["name"], str(d["pages"]), str(d["chunks"]), d["size"], d["status"]]
        for d in sess["documents"]
    ]
    
    summary = "\n".join(status_messages)
    return summary, doc_table, session_state


def chat_response(
    user_message: str,
    chat_history: List[Dict[str, str]],
    custom_groq_key: str,
    selected_model: str,
    temperature: float,
    session_state: str
) -> Tuple[str, List[Dict[str, str]], str]:
    if not user_message or not user_message.strip():
        return "", chat_history, ""

    sess = get_or_create_session(session_state)
    user_id = sess["user_id"]
    kb_id = sess["kb_id"]
    conv_id = sess["conversation_id"]

    # Temporarily apply custom Groq key if supplied
    if custom_groq_key and custom_groq_key.strip():
        settings.GROQ_API_KEY = custom_groq_key.strip()
    if selected_model:
        settings.GROQ_MODEL = selected_model
    settings.GROQ_TEMPERATURE = float(temperature)

    # Format history for RAG pipeline (supports dicts and tuples)
    history_tuples = []
    if isinstance(chat_history, list):
        for msg in chat_history:
            if isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role in ["user", "assistant"] and content:
                    history_tuples.append({"role": role, "content": str(content)})
            elif isinstance(msg, (list, tuple)) and len(msg) >= 2:
                u, a = msg[0], msg[1]
                if u:
                    history_tuples.append({"role": "user", "content": str(u)})
                if a:
                    history_tuples.append({"role": "assistant", "content": str(a)})

    # Execute Advanced RAG pipeline
    try:
        response = rag_pipeline.execute(
            query=user_message.strip(),
            user_id=user_id,
            kb_id=kb_id,
            conversation_id=conv_id,
            conversation_history=history_tuples[-6:] if history_tuples else []
        )

        answer_text = response.answer

        # Format citations into expandable markdown
        if response.citations:
            answer_text += "\n\n---\n### 📚 Sources & Citations\n"
            for idx, cit in enumerate(response.citations, 1):
                page_str = f" • Page {cit.page_number}" if cit.page_number else ""
                snippet = cit.snippet.replace("\n", " ").strip()
                answer_text += f"> **[{idx}] {cit.filename}{page_str}**\n> *\"{snippet}\"*\n\n"

        # Format metadata badge
        meta = response.metadata
        meta_info = (
            f"⚡ **Route:** `{meta.get('route', 'DIRECT')}` | "
            f"⏱️ **Latency:** `{meta.get('latency_seconds', 0):.2f}s` | "
            f"📄 **Candidates:** `{meta.get('candidates_retrieved', 0)}` | "
            f"🎯 **Top Passages:** `{meta.get('top_chunks_used', 0)}`"
        )
        if meta.get("crag_status"):
            meta_info += f" | 🛡️ **CRAG Status:** `{meta.get('crag_status')}`"

        # Append user message and assistant answer in compatible format
        if chat_history and isinstance(chat_history[0], (list, tuple)):
            chat_history.append((user_message, answer_text))
        else:
            chat_history.append({"role": "user", "content": user_message})
            chat_history.append({"role": "assistant", "content": answer_text})

        return "", chat_history, meta_info

    except Exception as e:
        logger.error(f"Chat pipeline error: {str(e)}")
        error_msg = f"⚠️ **Error:** {str(e)}\n\n*Please ensure a valid `GROQ_API_KEY` is configured in Space Secrets or Settings.*"
        if chat_history and isinstance(chat_history[0], (list, tuple)):
            chat_history.append((user_message, error_msg))
        else:
            chat_history.append({"role": "user", "content": user_message})
            chat_history.append({"role": "assistant", "content": error_msg})
        return "", chat_history, "⚠️ Pipeline execution error."


def reset_conversation(session_state: str) -> Tuple[List[Dict[str, str]], str, str]:
    new_id = str(uuid.uuid4())
    SESSION_DATA[new_id] = {
        "user_id": uuid.uuid4(),
        "kb_id": uuid.uuid4(),
        "conversation_id": uuid.uuid4(),
        "documents": [],
        "messages": []
    }
    return [], "Knowledge base & chat reset successfully.", new_id


# --- Modern Custom CSS ---
CUSTOM_CSS = """
/* Nexus AI Modern Glassmorphism Styling */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    background: radial-gradient(circle at 10% 20%, rgb(18, 20, 32) 0%, rgb(10, 11, 18) 90.2%);
    color: #e2e8f0;
}

#header-box {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15));
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    backdrop-filter: blur(12px);
}

.title-badge {
    background: linear-gradient(135deg, #6366f1, #a855f7);
    color: white;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 1px;
    display: inline-block;
    margin-bottom: 8px;
}

#chatbot-container {
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(15, 17, 26, 0.7);
}

.meta-status-box {
    font-size: 12px;
    color: #94a3b8;
    padding: 6px 12px;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.06);
    margin-top: 6px;
}

.send-btn {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
}

.reset-btn {
    background: rgba(239, 68, 68, 0.1) !important;
    color: #f87171 !important;
    border: 1px solid rgba(239, 68, 68, 0.2) !important;
}
"""

# --- Build Gradio Interface ---
with gr.Blocks(title="Nexus AI — Enterprise Knowledge Assistant") as demo:
    session_state = gr.State(value=lambda: str(uuid.uuid4()))

    with gr.Column(elem_id="header-box"):
        gr.HTML("""
        <div>
            <span class="title-badge">Enterprise Multi-Tenant RAG</span>
            <h1 style="margin: 0; font-size: 28px; font-weight: 800; background: linear-gradient(to right, #ffffff, #c7d2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                🧠 Nexus AI — Knowledge Assistant
            </h1>
            <p style="margin: 6px 0 0 0; color: #94a3b8; font-size: 14px;">
                Advanced Retrieval-Augmented Generation with <b>BGE Dense Embeddings</b> + <b>BM25 Lexical Matching</b> + <b>Cross-Encoder Reranking</b> + <b>Corrective Self-Reflection (CRAG)</b> + <b>Groq LPU Generation</b>.
            </p>
        </div>
        """)

    with gr.Row():
        # Left Column: Document Ingestion & KB Manager
        with gr.Column(scale=1):
            with gr.Accordion("📂 Document Manager & Ingestion", open=True):
                gr.Markdown("Upload documents (`PDF`, `DOCX`, `TXT`, `MD`, `CSV`) to index into your private knowledge base.")
                file_upload = gr.File(
                    label="Upload Knowledge Documents",
                    file_types=[".pdf", ".docx", ".doc", ".txt", ".md", ".csv"],
                    file_count="multiple",
                    height=140
                )
                upload_btn = gr.Button("⚡ Parse & Index into Vector Store", variant="primary")
                upload_status = gr.Markdown(value="*Upload documents above to index.*")
                
                doc_table = gr.Dataframe(
                    headers=["File Name", "Pages", "Chunks", "Size", "Status"],
                    datatype=["str", "str", "str", "str", "str"],
                    value=[],
                    label="Active Indexed Documents",
                    interactive=False
                )

            with gr.Accordion("⚙️ LLM & Retrieval Settings", open=False):
                groq_api_key_input = gr.Textbox(
                    label="Groq API Key (Optional override)",
                    placeholder="gsk_... (leave empty to use Space secret)",
                    type="password"
                )
                model_dropdown = gr.Dropdown(
                    label="Groq LLM Model",
                    choices=[
                        "llama-3.3-70b-versatile",
                        "llama-3.1-8b-instant",
                        "mixtral-8x7b-32768",
                        "gemma2-9b-it"
                    ],
                    value="llama-3.3-70b-versatile"
                )
                temperature_slider = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.1,
                    step=0.05,
                    label="Temperature (Creativity vs Strict Grounding)"
                )
                reset_kb_btn = gr.Button("🗑️ Clear Session & Knowledge Base", elem_classes=["reset-btn"])

            with gr.Accordion("ℹ️ Architecture & Capabilities", open=False):
                gr.Markdown("""
                - **Routing:** Direct QA, HyDE (*Hypothetical Document Embeddings*), Multi-turn Rewriter
                - **Dense Embedding:** `BAAI/bge-small-en-v1.5` (384-dim FastEmbed)
                - **Sparse Search:** `BM25Okapi` Exact Lexical Matching
                - **Fusion:** Reciprocal Rank Fusion (RRF with k=60)
                - **Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2`
                - **Validation:** Corrective RAG (CRAG) with confidence scoring
                """)

        # Right Column: Interactive Chat Interface
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="Conversational Knowledge Interface",
                height=520,
                elem_id="chatbot-container"
            )
            
            meta_status = gr.Markdown(
                value="⚡ *Nexus AI RAG Pipeline ready.*",
                elem_classes=["meta-status-box"]
            )

            with gr.Row():
                user_input = gr.Textbox(
                    placeholder="Ask anything about your uploaded documents or enterprise topics...",
                    label="Your Query",
                    lines=2,
                    max_lines=6,
                    scale=5,
                    autofocus=True
                )
                submit_btn = gr.Button("🚀 Ask", variant="primary", scale=1, elem_classes=["send-btn"])

            with gr.Row():
                gr.Examples(
                    examples=[
                        ["Summarize the key takeaways and main points from the uploaded documents."],
                        ["What are the security protocols, compliance requirements, and authentication mechanisms described in the text?"],
                        ["Can you explain the deployment workflow step by step with exact citations?"],
                        ["What are the prerequisites, architecture components, and performance benchmarks mentioned?"]
                    ],
                    inputs=user_input,
                    label="💡 Example Knowledge Queries"
                )

    # --- Event Bindings ---
    upload_btn.click(
        fn=process_uploaded_files,
        inputs=[file_upload, session_state],
        outputs=[upload_status, doc_table, session_state]
    )

    submit_btn.click(
        fn=chat_response,
        inputs=[user_input, chatbot, groq_api_key_input, model_dropdown, temperature_slider, session_state],
        outputs=[user_input, chatbot, meta_status]
    )

    user_input.submit(
        fn=chat_response,
        inputs=[user_input, chatbot, groq_api_key_input, model_dropdown, temperature_slider, session_state],
        outputs=[user_input, chatbot, meta_status]
    )

    reset_kb_btn.click(
        fn=reset_conversation,
        inputs=[session_state],
        outputs=[chatbot, meta_status, session_state]
    ).then(
        fn=lambda: (None, [], "*Knowledge base cleared.*"),
        outputs=[file_upload, doc_table, upload_status]
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False
    )
