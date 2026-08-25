import streamlit as st
from typing import List, Dict, Any


def render_citations(citations: List[Dict[str, Any]], metadata: Dict[str, Any]):
    if not citations and not metadata:
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        if citations:
            with st.expander(f"📚 Sources & Citations ({len(citations)})", expanded=False):
                for idx, c in enumerate(citations, start=1):
                    doc_name = c.get("document_name", "Unknown document")
                    page = c.get("page_number", 1)
                    snippet = c.get("snippet", "")
                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.6rem 0.8rem; border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid #3B82F6;">
                        <div style="font-weight: 600; font-size: 0.85rem; color: #E2E8F0;">
                            [Source {idx}] 📄 {doc_name} <span style="color: #94A3B8; font-weight: normal;">(Page {page})</span>
                        </div>
                        <div style="font-size: 0.8rem; color: #CBD5E1; margin-top: 0.3rem; line-height: 1.3;">
                            "{snippet}"
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    with col2:
        if metadata:
            with st.expander("⚡ RAG Telemetry", expanded=False):
                route = metadata.get("route", "N/A")
                attempts = metadata.get("retrieval_attempts", 1)
                candidates = metadata.get("candidates_retrieved", 0)
                used = metadata.get("top_chunks_used", 0)
                latency = metadata.get("latency_seconds", 0.0)
                crag = metadata.get("crag_status", "N/A")
                transformed = metadata.get("transformed_query")

                st.markdown(f"""
                <div style="font-size: 0.8rem; line-height: 1.6; color: #94A3B8;">
                    <div><b>Route:</b> <span style="color: #38BDF8;">{route}</span></div>
                    <div><b>Latency:</b> <span style="color: #4ADE80;">{latency}s</span></div>
                    <div><b>Hybrid Candidates:</b> {candidates}</div>
                    <div><b>Reranked Top-K:</b> {used}</div>
                    <div><b>CRAG Status:</b> <span style="color: #FBBF24;">{crag}</span></div>
                    <div><b>Retrieval Attempts:</b> {attempts}</div>
                </div>
                """, unsafe_allow_html=True)

                if transformed:
                    st.markdown(f"<div style='font-size: 0.75rem; color: #64748B; margin-top: 0.3rem;'><b>Rewritten Query:</b><br><i>{transformed}</i></div>", unsafe_allow_html=True)
