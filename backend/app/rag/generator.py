import re
from typing import List, Dict, Optional, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.rag import ScoredChunk, Citation
from backend.app.services.llm_service import llm_service


GENERATOR_SYSTEM_PROMPT = """You are an Enterprise AI Knowledge Assistant.
Your mission is to provide accurate, truthful, and helpful answers strictly grounded in the provided document sources.

Strict Instructions:
1. Grounding: Rely ONLY on the provided context sources below to answer the user's question.
2. No Hallucination: Do NOT fabricate facts, infer beyond what is written, or assume details not present in the sources.
3. Insufficient Context: If the answer cannot be found in the provided sources, state clearly and politely: "I could not find sufficient information in the knowledge base documents to answer this question."
4. Citations: When making a factual claim, cite the source using the exact format `[Source N]`.
5. Structure: Use clear formatting, bullet points, and professional language.
"""


class AnswerGenerator:
    @staticmethod
    def build_context(chunks: List[ScoredChunk]) -> Tuple[str, List[Citation]]:
        if not chunks:
            return "No document context available.", []

        context_lines = []
        citations: List[Citation] = []

        for idx, chunk in enumerate(chunks, start=1):
            source_tag = f"[Source {idx}]"
            context_lines.append(
                f"{source_tag} File: '{chunk.filename}' (Page {chunk.page_number}, Chunk: {chunk.chunk_id})\n"
                f"{chunk.text}\n"
            )
            citations.append(
                Citation(
                    document_id=chunk.document_id,
                    document_name=chunk.filename,
                    page_number=chunk.page_number,
                    chunk_id=chunk.chunk_id,
                    snippet=chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
                )
            )

        return "\n".join(context_lines), citations

    @classmethod
    def generate_answer(
        cls,
        query: str,
        chunks: List[ScoredChunk],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        insufficient_context: bool = False
    ) -> Tuple[str, List[Citation]]:
        if insufficient_context or not chunks:
            return (
                "I could not find sufficient information in the knowledge base documents to answer this question.",
                []
            )

        context_text, citations = cls.build_context(chunks)

        history_messages = []
        if conversation_history:
            # Include recent history
            for msg in conversation_history[-settings.MAX_HISTORY_MESSAGES:]:
                history_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        user_content = (
            f"=== DOCUMENT CONTEXT ===\n{context_text}\n"
            f"=== END CONTEXT ===\n\n"
            f"Question: {query}"
        )
        history_messages.append({"role": "user", "content": user_content})

        try:
            answer = llm_service.generate_chat(
                messages=history_messages,
                system_prompt=GENERATOR_SYSTEM_PROMPT,
                model=settings.GROQ_MODEL,
                temperature=settings.GROQ_TEMPERATURE,
                max_tokens=settings.GROQ_MAX_TOKENS
            )

            # Filter citations to only those actually referenced or top relevant
            return answer, citations

        except Exception as e:
            logger.error(f"Answer generation error: {str(e)}")
            return f"Error generating answer: {str(e)}", citations


answer_generator = AnswerGenerator()
