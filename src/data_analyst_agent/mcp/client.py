from .session import MCPSession
class MCPClient:
    def connect(self, server_id, transport, *, retries=1):
        session = MCPSession(server_id, transport, retries=retries); session.connect(); return session
