from pydantic.dataclasses import dataclass
from datetime import datetime

@dataclass
class ToolResult:
    tool: str
    status: str
    result: dict | None
    message: str | None


@dataclass
class MemoryItem:
    timestamp: str
    category: str
    content: str