# Learning Notes

- Plan steps declare their expected tools and outputs, which lets the executor
  route tool calls deterministically and lets the validator reject mismatches.
- Tool output is parsed into typed results before later steps consume it.
- Long-term memory and knowledge retrieval are repository-backed so their
  storage backends can evolve independently.
- MCP and multi-agent packages are modular experiments prepared for runtime
  integration; the default CLI remains the single-agent LangGraph workflow.
- Never put API keys in source archives or issue uploads. Store them only in
  local environment variables, rotate exposed keys, and use provider secrets
  management in deployment.
