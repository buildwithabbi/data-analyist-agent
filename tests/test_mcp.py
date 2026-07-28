from data_analyst_agent.mcp.enums import Permission
from data_analyst_agent.mcp.manager import MCPManager
from data_analyst_agent.mcp.models import MCPServerConfig
from data_analyst_agent.mcp.transport import MCPTransport

class FakeTransport(MCPTransport):
    def __init__(self): self.connected = False
    def connect(self): self.connected = True
    def close(self): self.connected = False
    def list_tools(self): return [{"name":"search_repo", "description":"Search files", "inputSchema":{"type":"object"}}]
    def call_tool(self, name, arguments): return {"name": name, "arguments": arguments}

def test_mcp_manager_discovers_and_calls_capability():
    manager = MCPManager(); transport = FakeTransport()
    manager.connect(MCPServerConfig(id="filesystem", required_permissions={Permission.READ}), transport)
    assert manager.registry.capabilities()[0].name == "search_repo"
    assert manager.call_tool("search_repo", {"query":"TODO"})["arguments"]["query"] == "TODO"
    assert manager.metrics()["filesystem"].calls == 1
    manager.shutdown(); assert transport.connected is False
