from pydantic import BaseModel, Field
from .enums import Permission
class MCPToolCapability(BaseModel):
    name: str; description: str = ""; input_schema: dict = Field(default_factory=dict); server_id: str
class MCPResource(BaseModel):
    uri: str; name: str; description: str = ""; mime_type: str | None = None; server_id: str
class MCPPrompt(BaseModel):
    name: str; description: str = ""; server_id: str
class MCPServerConfig(BaseModel):
    id: str; required_permissions: set[Permission] = Field(default_factory=lambda: {Permission.READ})
class MCPMetrics(BaseModel):
    calls: int = 0; failures: int = 0; retries: int = 0; latency_ms: float = 0
