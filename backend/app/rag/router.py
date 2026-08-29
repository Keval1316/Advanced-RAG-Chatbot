from typing import List, Dict, Optional
from enum import Enum
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.llm_service import llm_service


class QueryRoute(str, Enum):
    DIRECT_QA = "DIRECT_QA"
    REWRITE = "REWRITE"
    HYDE = "HYDE"


ROUTER_SYSTEM_PROMPT = """You are an expert AI Query Router in an enterprise RAG system.
Your job is to analyze the user's latest query along with conversation history, and classify it into exactly one of three routing strategies:

1. REWRITE: Choose this if the user's question is a follow-up, contains pronouns (it, they, that, this, its), or references previous messages that require contextual resolution to be understood as a standalone search query.
2. HYDE: Choose this if the query is a high-level conceptual, architectural, or theoretical question where generating a hypothetical technical passage would significantly bridge the semantic gap for vector retrieval.
3. DIRECT_QA: Choose this if the query is already clear, specific, self-contained, and does not require rewriting.

Respond ONLY with the route name: DIRECT_QA, REWRITE, or HYDE. Do not include explanations.
"""


GREETINGS = {
    "hi", "hello", "hey", "hey there", "good morning", "good afternoon", "good evening",
    "who are you", "who are you?", "what can you do", "what can you do?", "help", "thanks", "thank you"
}


class QueryRouter:
    @staticmethod
    def route(query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> QueryRoute:
        clean_query = query.strip()
        history = conversation_history or []

        # Heuristic 1: Instant fast-path for chit-chat / greetings
        if clean_query.lower() in GREETINGS:
            logger.info(f"Query '{clean_query}' fast-routed to DIRECT_QA (greeting).")
            return QueryRoute.DIRECT_QA

        # Heuristic 2: If no history, standalone queries are DIRECT_QA by default (0ms)
        if not history:
            return QueryRoute.DIRECT_QA

        # Heuristic 3: If history is present and query is short with ambiguous pronouns -> REWRITE
        pronouns = {"it", "its", "they", "them", "that", "this", "these", "those", "why?", "how?"}
        words = set(clean_query.lower().split())
        if len(words) <= 7 and bool(words & pronouns):
            logger.info(f"Query '{clean_query}' routed to REWRITE via conversational heuristic.")
            return QueryRoute.REWRITE

        prompt = f"Conversation History:\n"
        for msg in history[-3:]:
            prompt += f"{msg.get('role', 'user')}: {msg.get('content', '')}\n"

        prompt += f"\nCurrent Query: {clean_query}\n\nSelected Route:"

        try:
            decision = llm_service.generate(
                prompt=prompt,
                system_prompt=ROUTER_SYSTEM_PROMPT,
                model=settings.GROQ_ROUTER_MODEL,
                temperature=0.0,
                max_tokens=25
            ).strip().upper()

            if "REWRITE" in decision:
                route = QueryRoute.REWRITE
            elif "HYDE" in decision:
                route = QueryRoute.HYDE
            else:
                route = QueryRoute.DIRECT_QA

            logger.info(f"QueryRouter routed '{clean_query[:35]}...' to {route.value}")
            return route

        except Exception as e:
            logger.warning(f"Query router error: {str(e)}. Defaulting to DIRECT_QA.")
            return QueryRoute.DIRECT_QA


query_router = QueryRouter()
