from pydantic.dataclasses import dataclass


@dataclass
class ToolResult:
    tool: str
    status: str
    result: dict | None
    message: str | None
