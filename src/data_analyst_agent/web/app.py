"""Run with: streamlit run src/data_analyst_agent/web/app.py"""

from pathlib import Path
from hashlib import sha256
import json
import sqlite3
import sys
from time import time
from uuid import uuid4

# ``streamlit run src/data_analyst_agent/web/app.py`` executes this file
# directly, so add the source root just as the top-level CLI wrapper does.
SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pandas as pd
import streamlit as st
from langchain_core.messages import HumanMessage

from data_analyst_agent.agent.graph import graph
from data_analyst_agent.services.datasets import arrow_safe_preview, load_tabular_dataset
from data_analyst_agent.tools.analytics import PROJECT_ROOT, set_database_path


UPLOAD_DIR = PROJECT_ROOT / "database" / "uploads"
UPLOAD_RETENTION_SECONDS = 24 * 60 * 60


def _remove_expired_uploads(directory: Path, *, now: float | None = None) -> None:
    """Best-effort cleanup of generated uploads; never touches the sample DB."""
    if not directory.exists():
        return
    cutoff = (time() if now is None else now) - UPLOAD_RETENTION_SECONDS
    for candidate in directory.glob("*.db"):
        try:
            if candidate.stat().st_mtime < cutoff:
                candidate.unlink()
        except OSError:
            continue


def _show_dataset(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        preview = pd.read_sql_query("SELECT * FROM sales LIMIT 100", connection)
    st.caption(f"{len(preview)} preview rows · active database: `{path.name}`")
    # Do not use ``st.dataframe`` here: some CSVs contain mixed values (for
    # example floats and empty strings in one column), which can crash PyArrow
    # in certain local Streamlit builds. Escaped HTML has no Arrow dependency.
    st.markdown(
        arrow_safe_preview(preview).to_html(index=False, escape=True),
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Agentic Data Analyst", page_icon="📊", layout="wide")
    st.title("📊 Agentic AI Data Analyst")
    st.caption("Upload tabular data, ask a question, and inspect the agent’s evidence and execution trace.")
    if "database_path" not in st.session_state:
        st.session_state.database_path = PROJECT_ROOT / "database" / "sales.db"
    _remove_expired_uploads(UPLOAD_DIR)

    with st.sidebar:
        st.header("Dataset")
        upload = st.file_uploader("CSV or Excel", type=["csv", "xls", "xlsx"])
        if upload and st.button("Create database", type="primary"):
            safe_name = "".join(char if char.isalnum() else "_" for char in Path(upload.name).stem)
            content = upload.getvalue()
            digest = sha256(content).hexdigest()[:12]
            target = UPLOAD_DIR / f"{safe_name}_{digest}_{uuid4().hex}.db"
            try:
                path, rows, columns = load_tabular_dataset(content, upload.name, target)
                st.session_state.database_path = path
                st.success(f"Created {path.name} with {rows:,} rows and {len(columns)} columns.")
            except (ValueError, pd.errors.ParserError) as error:
                st.error(str(error))
        if st.button("Use bundled sales sample"):
            st.session_state.database_path = PROJECT_ROOT / "database" / "sales.db"
        try:
            _show_dataset(Path(st.session_state.database_path))
        except (OSError, ValueError, sqlite3.Error) as error:
            st.error(f"The selected dataset cannot be opened: {error}")

    question = st.text_area(
        "What would you like to analyze?",
        placeholder="Compare monthly sales and profit, then create a chart.",
        height=90,
    )
    if st.button("Analyze", type="primary", disabled=not question.strip()):
        set_database_path(st.session_state.database_path)
        with st.status("Planning, querying, validating, and analyzing…", expanded=True) as status:
            try:
                result = graph.invoke({"messages": [HumanMessage(content=question)], "trace": []}, config={"recursion_limit": 100})
            except Exception as error:
                status.update(label="Analysis failed", state="error")
                if "rate_limit" in str(error).lower() or "rate limit" in str(error).lower():
                    st.warning("Groq's rate limit was reached. Wait for the period shown in the error, then run the analysis again.")
                st.error(
                    "The analysis could not complete. Check that GROQ_API_KEY is set "
                    f"and try again. Details: {error}"
                )
                return
            status.update(label="Analysis complete", state="complete")
        st.subheader("Answer")
        st.markdown(str(result["messages"][-1].content))
        artifacts = result.get("artifacts", [])
        for artifact in artifacts:
            if artifact.type == "CHART":
                chart_path = PROJECT_ROOT / artifact.payload.get("chart_path", "")
                if chart_path.is_file(): st.image(str(chart_path), caption=artifact.payload.get("title", "Chart"))
        with st.expander("Execution trace"):
            st.code("\n".join(result.get("trace", [])))
        with st.expander("Tool results"):
            st.json([item.result or {"tool": item.tool, "message": item.message} for item in result.get("tool_results", [])])


if __name__ == "__main__":
    main()
