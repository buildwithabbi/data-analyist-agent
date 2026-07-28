from .models import MCPPrompt, MCPResource, MCPToolCapability


class MCPRegistry:
    def __init__(self):
        self.tools = {}
        self.resources = {}
        self.prompts = {}
        self.servers = {}

    def register(self, server_id, transport):
        self.servers[server_id] = transport
        for item in transport.list_tools():
            capability = MCPToolCapability(
                name=item["name"],
                description=item.get("description", ""),
                input_schema=item.get("inputSchema", {}),
                server_id=server_id,
            )
            if capability.name in self.tools:
                raise ValueError(f"Duplicate MCP capability: {capability.name}")
            self.tools[capability.name] = capability
        for item in transport.list_resources():
            self.resources[item["uri"]] = MCPResource(
                uri=item["uri"],
                name=item.get("name", item["uri"]),
                description=item.get("description", ""),
                mime_type=item.get("mimeType"),
                server_id=server_id,
            )
        for item in transport.list_prompts():
            self.prompts[f"{server_id}:{item['name']}"] = MCPPrompt(
                name=item["name"],
                description=item.get("description", ""),
                server_id=server_id,
            )

    def capabilities(self):
        return list(self.tools.values())

    def resources_summary(self):
        return list(self.resources.values())

    def prompts_summary(self):
        return list(self.prompts.values())

    def server_ids(self):
        return list(self.servers.keys())
