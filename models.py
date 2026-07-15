from pydantic.dataclasses import dataclass
from pydantic import Field


@dataclass
class ToolResult:
    tool: str
    status: str
    result: dict | None = None
    message: str | None = None


@dataclass
class Plan:
    goal: str
    steps: list[str]
    current_step: int = 0


@dataclass(kw_only=True)
class MemoryItem:
    content: str
    importance: float = Field(ge=0.0, le=1.0)
    category: str
    timestamp: str
