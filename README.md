# data-analyist-agent
## Setup Instructions

Follow these steps to set up the project locally:

### 1. Create a Virtual Environment
Create a isolated Python virtual environment named `.venv`:

**On Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```
```
Power Shell
.venv\Scripts\Activate.ps1
```
Install requirements.txt
```
pip install --upgrade pip
pip install -r requirements.txt
```
# Agentic AI Data Analyst

Project documentation: [Project Guide](docs/project-guide.md) and
[Architecture](docs/architecture.md).

## Web dashboard

Install dependencies, then launch the Streamlit interface from the repository
root:

```bash
pip install -r requirements.txt
streamlit run src/data_analyst_agent/web/app.py
```

The dashboard lets you upload CSV/XLS/XLSX datasets, creates an isolated local
SQLite database for each upload, accepts natural-language analysis requests,
and shows the answer, generated charts, tool outputs, and execution trace.

The CLI remains available for scripted usage:

```bash
python app.py "Show monthly sales trends"
```

The current Groq model is `llama-3.3-70b-versatile`. To select another model,
change the `MODEL_NAME` assignment in `src/data_analyst_agent/core/llm.py`.
