import json
import re
from typing import List, Dict, Optional, Any
from groq import Groq
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import LLMServiceException

FALLBACK_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
    "openai/gpt-oss-20b",
    "groq/compound",
    "groq/compound-mini",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]

DEFAULT_KEYS: List[str] = []


def clean_thinking_process(text: str) -> str:
    """Removes <think>...</think> tags and raw chain-of-thought scratchpad artifacts."""
    if not text:
        return ""
    # 1. Remove <think> XML tags
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"^<think>[\s\S]*?(?:\n\n|$)", "", cleaned, flags=re.IGNORECASE).strip()

    # 2. Remove markdown thinking process blocks
    pattern = r"^(?:Here(?:\'s| is) a thinking process|Thinking Process:|Analysis:)"
    if re.search(pattern, cleaned.strip(), re.IGNORECASE):
        sections = [s.strip() for s in cleaned.split("\n\n") if s.strip()]
        valid = []
        for s in sections:
            if re.match(r"^(?:Here(?:\'s| is) a thinking process|Analyze User Input|Identify Constraints|Formulate Response|Output Generation|Check against constraints|Plan:|Step \d+:|Ready\.)", s, re.IGNORECASE):
                continue
            valid.append(s)
        if valid:
            cleaned = "\n\n".join(valid).strip()

    # 3. Clean leading Output/Response markers
    cleaned = re.sub(r"^(?:Output|Response|Final Response|Answer):\s*", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"</think>", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned or text.strip()


class LLMService:
    _instance = None
    _clients: List[Groq] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
        return cls._instance

    def get_api_keys(self) -> List[str]:
        keys = []
        if isinstance(settings.GROQ_API_KEYS, list):
            keys = list(settings.GROQ_API_KEYS)
        elif isinstance(settings.GROQ_API_KEYS, str):
            try:
                parsed = json.loads(settings.GROQ_API_KEYS)
                if isinstance(parsed, list):
                    keys = parsed
            except Exception:
                keys = [k.strip() for k in settings.GROQ_API_KEYS.split(",") if k.strip()]

        if not keys and settings.GROQ_API_KEY:
            keys.append(settings.GROQ_API_KEY)

        for default_key in DEFAULT_KEYS:
            if default_key not in keys:
                keys.append(default_key)

        return [k for k in keys if k]

    def get_clients(self) -> List[Groq]:
        keys = self.get_api_keys()
        clients = []
        for key in keys:
            try:
                clients.append(Groq(api_key=key))
            except Exception as e:
                logger.warning(f"Could not init Groq client for key {key[:10]}...: {str(e)}")
        return clients

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        clients = self.get_clients()
        if not clients:
            return f"Answer based on available knowledge base: {prompt}"

        models_to_try = [model or settings.GROQ_MODEL] + [m for m in FALLBACK_MODELS if m != (model or settings.GROQ_MODEL)]
        selected_temp = temperature if temperature is not None else settings.GROQ_TEMPERATURE
        selected_max_tokens = max_tokens or settings.GROQ_MAX_TOKENS

        anti_cot_note = "\n\nCRITICAL: Output ONLY the direct final answer. Never expose or output any internal chain of thought, reasoning scratchpad, analysis steps, or <think> tags."
        final_sys_prompt = (system_prompt + anti_cot_note) if system_prompt else ("You are a helpful AI assistant." + anti_cot_note)

        messages = [
            {"role": "system", "content": final_sys_prompt},
            {"role": "user", "content": prompt}
        ]

        last_err = None
        for client in clients:
            for candidate_model in models_to_try:
                try:
                    completion = client.chat.completions.create(
                        model=candidate_model,
                        messages=messages,
                        temperature=selected_temp,
                        max_tokens=selected_max_tokens
                    )
                    raw_content = completion.choices[0].message.content.strip()
                    return clean_thinking_process(raw_content)
                except Exception as e:
                    last_err = e
                    logger.warning(f"Groq generation failed with model '{candidate_model}': {str(e)}. Retrying next...")

        raise LLMServiceException(message=f"All Groq API keys and candidate models failed: {str(last_err)}")

    def generate_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        clients = self.get_clients()
        if not clients:
            last_msg = messages[-1]["content"] if messages else ""
            return f"Answer based on context: {last_msg}"

        models_to_try = [model or settings.GROQ_MODEL] + [m for m in FALLBACK_MODELS if m != (model or settings.GROQ_MODEL)]
        selected_temp = temperature if temperature is not None else settings.GROQ_TEMPERATURE
        selected_max_tokens = max_tokens or settings.GROQ_MAX_TOKENS

        anti_cot_note = "\n\nCRITICAL: Output ONLY the direct final answer. Never expose or output any internal chain of thought, reasoning scratchpad, analysis steps, or <think> tags."
        final_sys_prompt = (system_prompt + anti_cot_note) if system_prompt else ("You are a helpful AI assistant." + anti_cot_note)

        formatted_messages = [{"role": "system", "content": final_sys_prompt}]
        formatted_messages.extend(messages)

        last_err = None
        for client in clients:
            for candidate_model in models_to_try:
                try:
                    completion = client.chat.completions.create(
                        model=candidate_model,
                        messages=formatted_messages,
                        temperature=selected_temp,
                        max_tokens=selected_max_tokens
                    )
                    raw_content = completion.choices[0].message.content.strip()
                    return clean_thinking_process(raw_content)
                except Exception as e:
                    last_err = e
                    logger.warning(f"Groq chat generation failed with model '{candidate_model}': {str(e)}. Retrying next...")

        raise LLMServiceException(message=f"All Groq API keys and candidate models failed: {str(last_err)}")


llm_service = LLMService()
