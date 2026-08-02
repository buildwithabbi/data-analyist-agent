# Project Guide: Agentic AI Data Analyst

## Purpose

Agentic AI Data Analyst answers natural-language questions about a tabular
dataset. It turns a request into a small execution plan, queries a local
SQLite database, optionally generates a chart, validates every tool result,
and produces a data-grounded response. It can be used from the command line
or through a Streamlit dashboard.

The bundled dataset is `database/sales.db`, which contains a `sales` table.
The dashboard can also convert an uploaded CSV, XLS, or XLSX file into an
isolated SQLite database and use it for the current session.

## Quick start

The project requires Python 3.11 or newer and a Groq API key. The language
model configuration reads `GROQ_API_KEY` from the environment.

```bash
python3 -m venv .venv
source .venv/bin/activate             # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
export GROQ_API_KEY="your-key"        # PowerShell: $env:GROQ_API_KEY="your-key"
```

Run one request from the repository root:

```bash
python app.py "Show monthly sales trends and create a chart"
```

Alternatively, install the package in editable mode and use either supported
entry point:

```bash
pip install -e .
data-analyst-agent "Which product category has the highest sales?"
python -m data_analyst_agent "Which product category has the highest sales?"
```

Start the dashboard with:

```bash
streamlit run src/data_analyst_agent/web/app.py
```

Keep secrets in your shell, a local untracked `.env` file, or deployment
secret management. Do not commit API keys.

## What happens to a request

The live request path is:

```text
CLI (`app.py`) or Streamlit UI
             |
             v
       LangGraph workflow
             |
  memory retrieval + knowledge retrieval
             |
             v
          planner
             |
             v
          executor -------- tool call ------> `run_sql` / `generate_chart`
             ^                                      |
             |                                      v
             +---- repair <--- reflection <--- validator
                                      |
                                      v
                              durable-memory update
                                      |
                                      v
                                     end
```

More precisely, the graph begins at `memory`, then runs `planner` and
`executor`. The executor either calls a registered tool or, for the final
summary step, asks the model for a response. The `validator` converts tool
output into typed results, records evidence, and advances the plan only when
the output satisfies the step contract. `reflection` decides whether to run
the next step, make a bounded repair attempt, persist a useful episode to
memory, or stop. The graph has a recursion limit of 100 in both interfaces.

## Runtime components

| Component | Responsibility | Main location |
| --- | --- | --- |
| Entry points | Parse a CLI question or launch the web UI. | `app.py`, `cli.py`, `web/app.py` |
| Graph and state | Defines node order, routing, and the shared state passed between nodes. | `agent/graph.py`, `agent/state.py` |
| Nodes | Retrieve context, plan, execute, validate, reflect, repair, and update memory. | `agent/nodes/` |
| Domain contracts | Typed plans, steps, tool results, artifacts, execution records, enums, and tool contracts. | `domain/` |
| Services | Planning, execution checks, context assembly, repair classification, and dataset conversion. | `services/` |
| Tools | Read-only SQL and PNG chart generation available to the running graph. | `tools/analytics.py` |
| Model integration | Configures the Groq chat model and safe retry behavior for malformed tool calls. | `core/` |
| Durable memory | Stores, ranks, deduplicates, retrieves, and manages past execution episodes. | `memory/` |
| Knowledge base | Ingests text, chunks and embeds it, then performs hybrid retrieval and reranking. | `knowledge/` |
| Utilities | Console JSON output and trace logging. | `utils/` |
| Tests | Unit and integration coverage for graph behaviour and independent modules. | `tests/` |

### Agent graph

`agent/graph.py` compiles the `DataAnalystAgent` LangGraph. Its state includes
messages, the plan, retrieved memory and knowledge, tool results, artifacts,
execution records, trace entries, and repair-loop fields.

The nodes have separate responsibilities:

- `memory_node` retrieves up to five relevant durable-memory items and five
  knowledge chunks for the user's question.
- `planner_node` uses the model to create structured `PlanStep` contracts. If
  the response is invalid JSON, it creates a safe fallback plan.
- `executor_node` works on one plan step at a time. Tool choice is determined
  by that step's contract; for charts it builds chart points directly from
  prior SQL results instead of asking the model to copy data.
- `validator_node` parses output, validates the tool result and dependencies,
  creates `DATASET` or `CHART` artifacts, and records the completed step.
- `reflection_node` classifies the latest outcome as successful, recoverable,
  or non-recoverable.
- `repair_node` records repair context and increments the repair count before
  returning to the executor when recovery is allowed.
- `memory_update_node` writes a durable episode only when the memory policy
  selects one for retention.

### Planning, execution, and repair

The planner's normal sequence is a SQL `QUERY`, an optional
`GENERATE_CHART`, then a final `SUMMARIZE`. Each step declares its expected
tool, output, inputs, and prerequisites. This prevents, for example, a chart
being created before a query has returned compatible data.

`services/execution.py` applies deterministic checks for tool contracts,
dependencies, result shapes, and downstream multi-series chart requirements.
`services/repair.py` categorizes failures and provides SQLite-specific repair
guidance. The executor's final summary is instructed to use only the compact
execution context and returned evidence.

### Analytical tools and safety

Only `run_sql` and `generate_chart` are registered in the live `TOOLS` list.
Schema text is supplied to the executor directly, avoiding unused tool
surfaces.

- `run_sql(query)` connects to the active SQLite database and returns JSON
  containing status, query, row count, and rows. It permits only queries that
  start with `SELECT` or `WITH` and rejects mutation and database-management
  keywords. It also detects the non-SQLite `EXTRACT()` syntax and returns a
  correction hint.
- `generate_chart(chart_type, title, data | series)` writes a PNG to `charts/`.
  It supports bar, line, pie, and scatter charts for one series; multi-series
  input is intentionally limited to line charts.

`set_database_path()` selects the database used by the analytical tools. The
dashboard calls it before each run, so uploaded datasets do not replace the
bundled sample database.

### Model configuration

`core/config.py` reads `GROQ_API_KEY`. `core/llm.py` creates a deterministic
Groq `ChatGroq` client (temperature `0`, 256 maximum tokens, 45-second
timeout). The active model is currently `llama-3.3-70b-versatile`; change the
`MODEL_NAME` assignment in that file to select one of the listed alternatives.

`safe_invoke()` retries a provider `BadRequestError` once with an explicit
tool-argument correction. Other failures return an empty tool-call response
so the graph can classify and handle the failure rather than terminating
unexpectedly.

## Data, files, and persistence

| Path | Contents | Lifecycle |
| --- | --- | --- |
| `database/sales.db` | Bundled SQLite sample database. | Source fixture; read by default. |
| `database/uploads/*.db` | Databases built from dashboard uploads. | Local generated files; ignored by Git. |
| `charts/*.png` | Generated chart artifacts. | Local generated files; ignored by Git. |
| `memory/agent_memory.db` | Durable execution memories. | Local generated file; ignored by Git. |
| `knowledge/knowledge.db` | Ingested documents and chunks. | Local generated file; ignored by Git. |

The dashboard's dataset loader normalizes column names, reads CSV or Excel
data with pandas, and writes a `sales` table to its selected upload database.
It also uses an HTML preview fallback to avoid PyArrow issues with mixed-type
columns.

## Memory and knowledge modules

The default graph actively uses both subsystems during its memory node.

- `memory/` provides repository-backed durable memory. `MemoryManager` is the
  public façade over SQLite storage, retrieval/ranking, writing, compression,
  lifecycle updates, and deduplication. Each episode is tagged with a SHA-256
  fingerprint of the active SQLite dataset, so only memories from the same
  dataset are retrieved. A matching memory guides planning, but the agent
  always reruns SQL and validates fresh results.
- `knowledge/` provides a small local knowledge base. `KnowledgeManager` can
  ingest a file or inline text, clean and chunk it, generate local hash
  embeddings, store it in SQLite, retrieve candidates with hybrid retrieval,
  and rerank the results. Retrieved chunks carry citation information for use
  in planning and context construction.

Neither the CLI nor dashboard currently exposes a document-ingestion control;
use `knowledge_manager.ingest(path)` or `knowledge_manager.add_text(text)`
from Python when adding knowledge programmatically.

### Response cache

Completed responses are cached by the active dataset fingerprint and a
normalized exact question. Repeating the same question for unchanged data
returns the cached answer and chart without calling the model or executing
SQL. Use **Refresh analysis** in the dashboard or `--refresh` in the CLI to
bypass the cache. Similar but non-identical questions still run the agent and
may use same-dataset durable memory as planning guidance.

## Extension modules

These packages are implemented and tested independently but are not wired
into the default CLI/Streamlit graph. They are useful foundations for future
integration, not services that must be configured to run the application.

| Package | Components | Intended role |
| --- | --- | --- |
| `mcp/` | Client, transport abstraction, sessions, registry, discovery, permissions, and tool/resource adapters. | Discover and expose Model Context Protocol server capabilities under a permission policy. |
| `multi_agent/` | Orchestrator, scheduler, registry, shared context, message bus, task/message models, and planner/research/analysis/reviewer/response specialists. | Coordinate specialized agents over shared tasks and messages. |
| `platform/` | SDK façade, governance policy, observability manager, and evaluation engine/results. | Provide application-level governance, metrics/tracing hooks, and evaluation support. |

## Development and verification

Run the test suite from the repository root:

```bash
pytest
```

Individual test modules map closely to the implementation areas, for example
`test_execution_engine.py`, `test_repair_flow.py`, `test_memory_manager.py`,
`test_knowledge.py`, `test_mcp.py`, and `test_multi_agent.py`.

To regenerate the workflow image, use:

```bash
python scripts/visualize_graph.py
```

The Mermaid source is `docs/diagrams/agent_graph.mmd` and the rendered image
is `docs/diagrams/agent_graph.png`.

## Common issues

- **Missing or invalid API key:** set `GROQ_API_KEY` in the environment before
  launching the CLI or dashboard.
- **Rate-limit error:** wait for the provider's reset window and retry. The
  dashboard surfaces this situation separately.
- **SQL errors:** the agent must use SQLite syntax. Date expressions should
  use `strftime`, not `EXTRACT`.
- **No chart generated:** a chart requires compatible preceding SQL rows. For
  a single series, the executor needs a label/date/category field and a
  numeric field; multi-series charts need a label and each requested metric.
- **Wrong dataset:** in the dashboard, click **Create database** after
  uploading, then run the analysis. Click **Use bundled sales sample** to
  switch back.
