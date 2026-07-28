"""Run with: streamlit run src/data_analyst_agent/web/app.py"""

from pathlib import Path
import json
import sys

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


def _show_dataset(path: Path) -> None:
    import sqlite3
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

    with st.sidebar:
        st.header("Dataset")
        upload = st.file_uploader("CSV or Excel", type=["csv", "xls", "xlsx"])
        if upload and st.button("Create database", type="primary"):
            safe_name = "".join(char if char.isalnum() else "_" for char in Path(upload.name).stem)
            target = UPLOAD_DIR / f"{safe_name}.db"
            try:
                path, rows, columns = load_tabular_dataset(upload.getvalue(), upload.name, target)
                st.session_state.database_path = path
                st.success(f"Created {path.name} with {rows:,} rows and {len(columns)} columns.")
            except (ValueError, pd.errors.ParserError) as error:
                st.error(str(error))
        if st.button("Use bundled sales sample"):
            st.session_state.database_path = PROJECT_ROOT / "database" / "sales.db"
        _show_dataset(Path(st.session_state.database_path))

    question = st.text_area(
        "What would you like to analyze?",
        placeholder="Compare monthly sales and profit, then create a chart.",
        height=90,
    )
    if st.button("Analyze", type="primary", disabled=not question.strip()):
        set_database_path(st.session_state.database_path)
        with st.spinner("Planning, querying, validating, and analyzing…"):
            try:
                result = graph.invoke({"messages": [HumanMessage(content=question)], "trace": []}, config={"recursion_limit": 100})
            except Exception as error:
                st.error(f"Analysis failed: {error}")
                return
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
