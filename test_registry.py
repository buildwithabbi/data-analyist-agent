from registry import ToolRegistry
from console_output import print_json

registry = ToolRegistry()

print_json("REGISTERED TOOLS", registry.list_tools())
print_json("TOOL DESCRIPTIONS", {"descriptions": registry.describe_tools()})
