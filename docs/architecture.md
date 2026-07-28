# Architecture

The live CLI path is `app.py` → `data_analyst_agent.cli` → LangGraph. The
graph runs memory retrieval, planning, deterministic execution, tool output
validation, reflection, repair, and durable-memory updates.

Core runtime packages are `agent/`, `domain/`, `services/`, `tools/`,
`memory/`, and `knowledge/`. `mcp/`, `multi_agent/`, and `platform/` are
independent, tested platform modules. They expose extension points and SDKs,
but are not yet selected by the default CLI graph.

All database access is read-only through `run_sql`; external knowledge is
retrieved with cited chunks; durable memory is stored behind repository
interfaces.
