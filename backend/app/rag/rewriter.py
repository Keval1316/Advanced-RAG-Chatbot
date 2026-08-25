from typing import List, Dict, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.llm_service import llm_service


REWRITER_SYSTEM_PROMPT = """You are an expert Query Reformulation specialist in an enterprise RAG system.
Your task is to rewrite the user's latest question into a self-contained, unambiguous search query suitable for vector and lexical retrieval.

Rules:
1. Resolve all pronouns (it, they, that, this, its) using the provided conversation history.
2. Maintain the user's exact original question intent.
3. Do NOT answer the question.
4. Do NOT add extraneous facts or assumptions not mentioned in the context.
5. Return ONLY the rewritten query text with no preamble or explanation.
"""


class QueryRewriter:
    @staticmethod
    def rewrite(query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        history = conversation_history or []
        if not history:
            return query.strip()

        history_str = ""
        for msg in history[-6:]:
            history_str += f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}\n"

        user_prompt = (
            f"Conversation History:\n{history_str}\n"
            f"Current Follow-up Query: {query}\n\n"
            f"Rewritten Standalone Query:"
        )

        try:
            rewritten = llm_service.generate(
                prompt=user_prompt,
                system_prompt=REWRITER_SYSTEM_PROMPT,
                model=settings.GROQ_ROUTER_MODEL,
                temperature=0.1,
                max_tokens=100
            ).strip()

            # Clean any wrapping quotes
            rewritten = rewritten.strip('"\'')
            logger.info(f"Rewrote query '{query}' -> '{rewritten}'")
            return rewritten if rewritten else query

        except Exception as e:
            logger.warning(f"Failed to rewrite query: {str(e)}. Using original query.")
            return query


query_rewriter = QueryRewriter()
