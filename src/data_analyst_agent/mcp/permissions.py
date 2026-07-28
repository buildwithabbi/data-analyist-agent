from .enums import Permission
class PermissionPolicy:
    def __init__(self, allowed: set[Permission] | None = None): self.allowed = allowed or {Permission.READ}
    def check(self, requested: set[Permission]) -> None:
        denied = requested - self.allowed
        if denied: raise PermissionError(f"MCP permissions denied: {', '.join(item.value for item in denied)}")
