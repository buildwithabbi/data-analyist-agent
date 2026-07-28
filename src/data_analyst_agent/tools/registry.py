from .analytics import TOOLS


class ToolRegistry:

    def __init__(self, mcp_manager=None):
        self.tools = {}

        for tool in TOOLS:
            self.tools[tool.name] = tool

        if mcp_manager:
            from ..mcp.adapters import adapt_mcp_tool
            for capability in mcp_manager.registry.capabilities():
                self.tools[capability.name] = adapt_mcp_tool(mcp_manager, capability)

    def list_tools(self):
        return list(self.tools.keys())

    def get_tool(self, name):
        return self.tools.get(name)

    def describe_tools(self):
        descriptions = []

        for tool in self.tools.values():
            descriptions.append(f"{tool.name}: {tool.description}")

        return "\n".join(descriptions)
