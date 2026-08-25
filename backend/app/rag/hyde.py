from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.llm_service import llm_service


HYDE_SYSTEM_PROMPT = """You are a technical knowledge synthesizer in a Hypothetical Document Embeddings (HyDE) pipeline.
Given a user query, generate a concise, realistic, and detailed hypothetical document passage (1-2 paragraphs) that would directly answer this question in a technical manual or handbook.

Rules:
1. Write in the formal style of an authoritative engineering or documentation guide.
2. Include typical terminology, technical structure, and expected concepts.
3. Output ONLY the hypothetical passage text. Do NOT add notes, headers, or metadata.
"""


class HyDEGenerator:
    @staticmethod
    def generate_hypothetical_document(query: str) -> str:
        prompt = f"User Question: {query}\n\nHypothetical Passage:"

        try:
            passage = llm_service.generate(
                prompt=prompt,
                system_prompt=HYDE_SYSTEM_PROMPT,
                model=settings.GROQ_MODEL,
                temperature=0.3,
                max_tokens=300
            ).strip()

            logger.info(f"Generated HyDE passage for query '{query[:35]}...' ({len(passage)} chars)")
            return passage

        except Exception as e:
            logger.warning(f"HyDE generation failed: {str(e)}. Falling back to raw query.")
            return query


hyde_generator = HyDEGenerator()
