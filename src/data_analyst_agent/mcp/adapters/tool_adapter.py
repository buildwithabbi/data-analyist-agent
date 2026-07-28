from langchain_core.tools import StructuredTool
from pydantic import create_model

def adapt_mcp_tool(manager, capability):
    fields = {name: (object, ...) for name in capability.input_schema.get("properties", {})}
    schema = create_model(f"MCP_{capability.name}", **fields)
    def invoke(**arguments): return manager.call_tool(capability.name, arguments)
    return StructuredTool.from_function(invoke, name=capability.name, description=capability.description, args_schema=schema)
