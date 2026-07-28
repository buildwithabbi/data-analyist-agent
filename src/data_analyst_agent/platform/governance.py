"""Basic governance primitives for masking PII and recording audit events."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


class GovernancePolicy:
    """Policy hooks for data handling and auditability."""

    def __init__(self) -> None:
        self.audit_log: list[dict[str, Any]] = []

    def mask_pii(self, text: str) -> str:
        masked = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[REDACTED_EMAIL]", text, flags=re.IGNORECASE)
        masked = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", masked)
        return masked

    def audit(self, actor: str, action: str, **metadata: Any) -> dict[str, Any]:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "metadata": metadata,
        }
        self.audit_log.append(entry)
        return entry
