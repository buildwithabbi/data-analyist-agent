from dataclasses import dataclass, field
@dataclass
class SharedContext:
    query: str; data: dict = field(default_factory=dict); traces: list[str] = field(default_factory=list); approved: bool = True
