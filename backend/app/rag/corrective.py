from typing import List, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.rag import ScoredChunk
from backend.app.services.llm_service import llm_service


CRAG_EVAL_SYSTEM_PROMPT = """You are an impartial relevance evaluator in an enterprise RAG system.
Your job is to assess if the provided retrieved document passages contain sufficient and relevant information to answer the user's question.

Evaluate the context and respond with:
- RELEVANT (if the context provides meaningful information to answer the question)
- INSUFFICIENT (if the context is completely unrelated, ambiguous, or lacks the necessary facts)

Respond ONLY with 'RELEVANT' or 'INSUFFICIENT'.
"""


class CorrectiveRAG:
    @staticmethod
    def evaluate_context(
        query: str,
        chunks: List[ScoredChunk],
        attempt: int = 1
    ) -> Tuple[str, bool]:
        """Evaluates whether retrieved passages are relevant and sufficient.
        Returns (evaluation_status: 'RELEVANT' | 'INSUFFICIENT', should_retry: bool)
        """
        if not chunks:
            logger.info("CRAG: No chunks retrieved.")
            should_retry = attempt < settings.MAX_RETRIEVAL_ATTEMPTS
            return "INSUFFICIENT", should_retry

        # Score-based check + LLM relevance verification
        highest_score = max(c.score for c in chunks)
        
        # If score is usable (cross-encoder logit >= -1.5 or hybrid score > 0.01), fast-path accept (0ms)
        if highest_score >= -1.5:
            logger.info(f"CRAG: Sufficient retrieval score ({highest_score:.3f}). Context accepted as RELEVANT.")
            return "RELEVANT", False

        # If score is very low/questionable, verify with fast LLM evaluator
        context_snippet = "\n---\n".join([f"[{c.filename}] {c.text[:250]}" for c in chunks[:3]])
        prompt = f"User Question: {query}\n\nRetrieved Context:\n{context_snippet}\n\nRelevance Assessment:"

        try:
            assessment = llm_service.generate(
                prompt=prompt,
                system_prompt=CRAG_EVAL_SYSTEM_PROMPT,
                model=settings.GROQ_ROUTER_MODEL,
                temperature=0.0,
                max_tokens=30
            ).strip().upper()

            is_relevant = "RELEVANT" in assessment
            should_retry = (not is_relevant) and (attempt < settings.MAX_RETRIEVAL_ATTEMPTS)

            logger.info(f"CRAG evaluation result: '{assessment}' (attempt {attempt}, retry={should_retry})")
            return ("RELEVANT" if is_relevant else "INSUFFICIENT"), should_retry

        except Exception as e:
            logger.warning(f"CRAG evaluation failed: {str(e)}. Assuming context is usable.")
            return "RELEVANT", False


corrective_rag = CorrectiveRAG()
