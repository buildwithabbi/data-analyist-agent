from dataclasses import dataclass, field
from datetime import datetime, timezone
@dataclass
class AgentMessage:
    event: str; sender: str; payload: dict; task_id: str = ""; timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
