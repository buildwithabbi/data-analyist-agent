"""
AI Security Guardrails Subsystem
Implements:
1. PII Masking/Redaction (Emails, Phone numbers, SSN, Credit Cards)
2. Prompt Injection & Jailbreak Defense
3. Semantic Intent Routing (Off-topic query filtering)
"""

import re
from typing import NamedTuple, List, Tuple


class GuardrailResult(NamedTuple):
    is_safe: bool
    sanitized_text: str
    intent: str
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    reason: str


class PIIMasker:
    """Detects and redacts Sensitive PII before sending prompts to external APIs."""

    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    CREDIT_CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
    SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    @classmethod
    def sanitize(cls, text: str) -> Tuple[str, List[str]]:
        masked_items = []
        sanitized = text

        if cls.EMAIL_REGEX.search(sanitized):
            sanitized = cls.EMAIL_REGEX.sub("[EMAIL_REDACTED]", sanitized)
            masked_items.append("Email Address")

        if cls.PHONE_REGEX.search(sanitized):
            sanitized = cls.PHONE_REGEX.sub("[PHONE_REDACTED]", sanitized)
            masked_items.append("Phone Number")

        if cls.SSN_REGEX.search(sanitized):
            sanitized = cls.SSN_REGEX.sub("[SSN_REDACTED]", sanitized)
            masked_items.append("SSN")

        if cls.CREDIT_CARD_REGEX.search(sanitized):
            sanitized = cls.CREDIT_CARD_REGEX.sub("[CREDIT_CARD_REDACTED]", sanitized)
            masked_items.append("Credit Card Number")

        return sanitized, masked_items


class SecurityGuardrails:
    """Guardrails engine for prompt injection defense & semantic intent classification."""

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
        r"system\s+prompt",
        r"you\s+are\s+now",
        r"drop\s+table",
        r"delete\s+from",
        r"truncate\s+table",
        r"alter\s+table",
        r"exec\s*\(",
        r"eval\s*\(",
        r"import\s+os",
        r"import\s+subprocess",
    ]

    OFF_TOPIC_KEYWORDS = [
        "recipe",
        "poem",
        "story",
        "joke",
        "song",
        "movie",
        "weather",
        "horoscope",
    ]

    @classmethod
    def evaluate_prompt(cls, user_prompt: str) -> GuardrailResult:
        prompt_lower = user_prompt.lower()

        # 1. Detect Prompt Injection & Malicious Commands
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, prompt_lower):
                return GuardrailResult(
                    is_safe=False,
                    sanitized_text=user_prompt,
                    intent="MALICIOUS_INJECTION",
                    risk_level="HIGH",
                    reason=f"Security Alert: Malicious pattern detected ('{pattern}'). Query blocked.",
                )

        # 2. Detect Off-Topic Queries
        is_off_topic = any(kw in prompt_lower for kw in cls.OFF_TOPIC_KEYWORDS)
        data_keywords = ["sales", "data", "profit", "chart", "table", "dataset", "query", "count", "revenue"]
        if is_off_topic and not any(dk in prompt_lower for dk in data_keywords):
            return GuardrailResult(
                is_safe=False,
                sanitized_text=user_prompt,
                intent="OFF_TOPIC",
                risk_level="MEDIUM",
                reason="Off-topic prompt: Please ask questions related to data analytics, sales, or charts.",
            )

        # 3. Apply PII Masking
        sanitized_prompt, masked_types = PIIMasker.sanitize(user_prompt)
        reason = (
            f"Prompt validated cleanly. Masked PII: {', '.join(masked_types)}"
            if masked_types
            else "Prompt validated cleanly."
        )

        return GuardrailResult(
            is_safe=True,
            sanitized_text=sanitized_prompt,
            intent="VALID_DATA_QUERY",
            risk_level="LOW",
            reason=reason,
        )
