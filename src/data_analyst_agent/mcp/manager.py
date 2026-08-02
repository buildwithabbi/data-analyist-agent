from .client import MCPClient
from .permissions import PermissionPolicy
from .registry import MCPRegistry


class MCPManager:
    def __init__(self, policy=None):
        self.policy = policy or PermissionPolicy()
        self.client = MCPClient()
        self.registry = MCPRegistry()
        self.sessions = {}

    def connect(self, config, transport):
        self.policy.check(config.required_permissions)
        session = self.client.connect(config.id, transport)
        self.sessions[config.id] = session
        self.registry.register(config.id, transport)
        return session

    def disconnect(self, server_id):
        session = self.sessions.pop(server_id, None)
        if session:
            session.close()

    def call_tool(self, name, arguments):
        capability = self.registry.tools[name]
        return self.sessions[capability.server_id].call_tool(name, arguments)

    def read_resource(self, uri):
        """Read a registered MCP resource through its connected server."""
        resource = self.registry.resources[uri]
        session = self.sessions.get(resource.server_id)
        if session is None:
            raise RuntimeError(f"MCP server {resource.server_id!r} is not connected.")
        if session.status.name != "CONNECTED":
            session.connect()
        return session.transport.read_resource(uri)

    def discover(self):
        return self.registry.capabilities()

    def summary(self):
        return {
            "servers": self.registry.server_ids(),
            "tools": [capability.model_dump() for capability in self.registry.capabilities()],
            "resources": [resource.model_dump() for resource in self.registry.resources_summary()],
            "prompts": [prompt.model_dump() for prompt in self.registry.prompts_summary()],
        }

    def metrics(self):
        return {server_id: session.metrics for server_id, session in self.sessions.items()}

    def shutdown(self):
        for server_id in list(self.sessions):
            self.disconnect(server_id)
