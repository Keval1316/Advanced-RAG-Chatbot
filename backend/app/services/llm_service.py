from typing import List, Dict, Optional, Any
from groq import Groq
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import LLMServiceException


class LLMService:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
        return cls._instance

    def get_client(self) -> Optional[Groq]:
        if self._client is None and settings.GROQ_API_KEY:
            try:
                self._client = Groq(api_key=settings.GROQ_API_KEY)
                logger.info(f"Initialized Groq client with model: {settings.GROQ_MODEL}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {str(e)}")
        return self._client

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        client = self.get_client()
        selected_model = model or settings.GROQ_MODEL
        selected_temp = temperature if temperature is not None else settings.GROQ_TEMPERATURE
        selected_max_tokens = max_tokens or settings.GROQ_MAX_TOKENS

        if not client:
            logger.warning("Groq API key not set or client unavailable. Returning deterministic response.")
            if "route" in prompt.lower() or "classifier" in (system_prompt or "").lower():
                return "DIRECT_QA"
            elif "rewrite" in (system_prompt or "").lower():
                return prompt.strip()
            elif "hypothetical" in (system_prompt or "").lower():
                return f"Passage containing relevant information regarding: {prompt}"
            elif "evaluate" in (system_prompt or "").lower() or "relevance" in (system_prompt or "").lower():
                return "RELEVANT"
            return f"Answer based on available knowledge base: {prompt}"

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            completion = client.chat.completions.create(
                model=selected_model,
                messages=messages,
                temperature=selected_temp,
                max_tokens=selected_max_tokens
            )
            return completion.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Groq LLM generation failed: {str(e)}")
            raise LLMServiceException(message=f"Groq API error: {str(e)}")

    def generate_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        client = self.get_client()
        selected_model = model or settings.GROQ_MODEL
        selected_temp = temperature if temperature is not None else settings.GROQ_TEMPERATURE
        selected_max_tokens = max_tokens or settings.GROQ_MAX_TOKENS

        if not client:
            last_msg = messages[-1]["content"] if messages else ""
            return f"Answer based on context: {last_msg}"

        try:
            formatted_messages = []
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            formatted_messages.extend(messages)

            completion = client.chat.completions.create(
                model=selected_model,
                messages=formatted_messages,
                temperature=selected_temp,
                max_tokens=selected_max_tokens
            )
            return completion.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Groq LLM chat completion failed: {str(e)}")
            raise LLMServiceException(message=f"Groq API chat error: {str(e)}")


llm_service = LLMService()
