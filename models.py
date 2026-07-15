from pydantic.dataclasses import dataclass


@dataclass
class ToolResult:
    tool: str
    status: str
    result: dict | None = None
    message: str | None = None
    

@dataclass
class MemoryItem:
    timestamp: str
    category: str
    content: str
