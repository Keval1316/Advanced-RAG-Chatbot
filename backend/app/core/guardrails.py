import re
from typing import Tuple, List
from backend.app.core.logging import logger

# Comprehensive multilingual blacklist (English, Hindi, Hinglish slangs & profanities)
BLOCKED_PATTERNS = [
    # Explicit Slangs & Profanity (English)
    r"\b(fuck|shit|bitch|bastard|asshole|cunt|dick|pussy|whore|slut|nigger|faggot)\b",
    r"\b(motherfucker|cock|mother\s*fucker|bullshit|jackass)\b",
    
    # Explicit Slangs & Profanity (Hindi / Hinglish)
    r"\b(chutiya|chutiye|madarchod|bhenchod|behenchod|bhosdike|bhosadi|gandu|harami|kamina)\b",
    r"\b(gaand|lauda|loda|lund|saala|kutta|chinal|randi|suar|bhadwe|bhadwa)\b",
    r"\b(bc|mc|bsdk|chutiyaap)\b",
    
    # Prompt Injections & Jailbreaks
    r"(ignore\s+all\s+(previous|prior)\s+instructions)",
    r"(reveal\s+(system\s+prompt|secret\s+key|api\s+key))",
    r"(system\s+override\s+mode)",
    r"(dan\s+mode|jailbreak)"
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]


class InputGuardrails:
    @staticmethod
    def evaluate(user_input: str) -> Tuple[bool, str]:
        """
        Validates user input against safety guardrails.
        Returns:
            (is_safe: bool, reason_or_cleaned_message: str)
        """
        if not user_input or not user_input.strip():
            return True, ""

        clean_text = user_input.strip()

        # Check against blacklist patterns
        for pattern in COMPILED_PATTERNS:
            if pattern.search(clean_text):
                logger.warning(f"Guardrail violation detected for input: '{clean_text[:40]}...'")
                return False, "I cannot fulfill this request as it contains inappropriate, offensive language or violates enterprise safety policies. Please maintain a professional conversation."

        return True, clean_text


guardrails = InputGuardrails()
