import re
from typing import List, Dict, Optional, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.rag import ScoredChunk, Citation
from backend.app.services.llm_service import llm_service


GENERATOR_SYSTEM_PROMPT = """You are Nexus AI, a brilliant, helpful, and friendly Enterprise AI Knowledge Assistant powered by Llama 3.3.
You can converse naturally in any language (English, Hindi, Hinglish, Spanish, etc.), explain concepts, write and debug code, and analyze enterprise documents.

Instructions:
1. When Document Context is provided below:
   - Provide answers grounded in the provided document sources.
   - Use source citations like `[Source N]` where appropriate.
2. When NO Document Context is provided or when the user is chatting generally (greetings, general questions, coding problems):
   - Answer directly, conversationally, and accurately in the user's language and tone without any artificial refusal.
3. Structure: Use clean markdown, bold terms, bullet points, and code blocks where helpful.
"""


class AnswerGenerator:
    @staticmethod
    def build_context(chunks: List[ScoredChunk], max_total_chars: int = 4500) -> Tuple[str, List[Citation]]:
        if not chunks:
            return "No document context available.", []

        context_lines = []
        citations: List[Citation] = []
        current_chars = 0

        # Use top 5 chunks max and enforce strict character ceiling
        for idx, chunk in enumerate(chunks[:5], start=1):
            chunk_text = chunk.text.strip()
            if current_chars + len(chunk_text) > max_total_chars and context_lines:
                # Include truncated portion if space remains
                remaining = max_total_chars - current_chars
                if remaining > 100:
                    chunk_text = chunk_text[:remaining] + "..."
                else:
                    break

            source_tag = f"[Source {idx}]"
            context_lines.append(
                f"{source_tag} File: '{chunk.filename}' (Page {chunk.page_number}, Chunk: {chunk.chunk_id})\n"
                f"{chunk_text}\n"
            )
            citations.append(
                Citation(
                    document_id=chunk.document_id,
                    document_name=chunk.filename,
                    page_number=chunk.page_number,
                    chunk_id=chunk.chunk_id,
                    snippet=chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
                )
            )
            current_chars += len(chunk_text)

        return "\n".join(context_lines), citations

    @classmethod
    def generate_answer(
        cls,
        query: str,
        chunks: List[ScoredChunk],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        insufficient_context: bool = False
    ) -> Tuple[str, List[Citation]]:
        citations: List[Citation] = []
        history_messages = []

        # Keep only the last 4 messages to save context budget
        if conversation_history:
            recent_history = conversation_history[-4:]
            for msg in recent_history:
                content = msg.get("content", "")
                # Truncate very long previous messages in history to save tokens
                if len(content) > 500:
                    content = content[:500] + "..."
                history_messages.append({
                    "role": msg.get("role", "user"),
                    "content": content
                })

        if chunks and not insufficient_context:
            context_text, citations = cls.build_context(chunks)
            user_content = (
                f"=== DOCUMENT CONTEXT ===\n{context_text}\n"
                f"=== END CONTEXT ===\n\n"
                f"Question: {query}"
            )
        else:
            user_content = query

        history_messages.append({"role": "user", "content": user_content})

        try:
            answer = llm_service.generate_chat(
                messages=history_messages,
                system_prompt=GENERATOR_SYSTEM_PROMPT,
                model=settings.GROQ_MODEL,
                temperature=settings.GROQ_TEMPERATURE,
                max_tokens=settings.GROQ_MAX_TOKENS
            )
            return answer, citations

        except Exception as e:
            logger.error(f"Answer generation error: {str(e)}")
            return f"Error generating answer: {str(e)}", citations


answer_generator = AnswerGenerator()
