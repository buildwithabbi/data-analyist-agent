from dataclasses import dataclass, field
from uuid import uuid4
@dataclass
class AgentTask:
    agent: str; payload: dict; dependencies: set[str] = field(default_factory=set); id: str = field(default_factory=lambda: str(uuid4())); retries: int = 0
