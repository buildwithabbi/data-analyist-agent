# Data Analyst Agent

A LangGraph-powered agent that queries the sales dataset and can generate charts.

## Project layout

```text
src/data_analyst_agent/
├── agent/       # LangGraph state, nodes, graph, and routing
├── core/        # Configuration and LLM client
├── domain/      # Shared data models
├── memory/      # In-session memory
├── services/    # Planning and context-building services
├── tools/       # SQL and chart tools
└── utils/       # Console and trace formatting
database/        # Source CSV, SQLite database, and database builder
tests/           # Automated checks
scripts/         # Developer utilities, such as graph visualization
docs/            # Architecture notes and diagrams
```

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip setuptools
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
```

Create or refresh the SQLite database from the source CSV:

```bash
.venv/bin/python database/create_db.py
```

Set `GROQ_API_KEY` in a `.env` file, then run the agent:

```bash
.venv/bin/python -m data_analyst_agent
```

You can also use the installed `data-analyst-agent` command. The legacy
`app.py` script remains as a compatibility entry point.

## Development

Run the lightweight checks directly (or install `pytest` and run `pytest`):

```bash
PYTHONPATH=src .venv/bin/python -c "from tests.test_registry import test_registry_exposes_registered_tools; test_registry_exposes_registered_tools()"
```

Regenerate workflow diagrams with:

```bash
.venv/bin/python scripts/visualize_graph.py
```
