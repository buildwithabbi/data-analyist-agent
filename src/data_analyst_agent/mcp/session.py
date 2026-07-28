from time import perf_counter
from .enums import SessionStatus
from .models import MCPMetrics
class MCPSession:
    def __init__(self, server_id, transport, *, retries=1): self.server_id, self.transport, self.retries, self.status, self.metrics = server_id, transport, retries, SessionStatus.DISCONNECTED, MCPMetrics()
    def connect(self): self.transport.connect(); self.status = SessionStatus.CONNECTED
    def close(self): self.transport.close(); self.status = SessionStatus.DISCONNECTED
    def call_tool(self, name, arguments):
        if self.status != SessionStatus.CONNECTED: self.connect()
        started = perf_counter()
        for attempt in range(self.retries + 1):
            try:
                result = self.transport.call_tool(name, arguments); self.metrics.calls += 1; self.metrics.latency_ms += (perf_counter()-started)*1000; return result
            except Exception:
                self.metrics.failures += 1
                if attempt == self.retries: self.status = SessionStatus.FAILED; raise
                self.metrics.retries += 1; self.connect()
