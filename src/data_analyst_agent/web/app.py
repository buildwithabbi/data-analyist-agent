"""Run with: streamlit run src/data_analyst_agent/web/app.py"""

from pathlib import Path
from hashlib import sha256
import json
import sqlite3
import sys
from datetime import datetime
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
from data_analyst_agent.core.llm import MODEL_NAME
from data_analyst_agent.services.datasets import arrow_safe_preview, load_tabular_dataset
from data_analyst_agent.services.response_cache import response_cache
from data_analyst_agent.tools.analytics import PROJECT_ROOT, active_dataset_id, set_database_path


UPLOAD_DIR = PROJECT_ROOT / "database" / "uploads"
UPLOAD_RETENTION_SECONDS = 24 * 60 * 60
DEFAULT_MODEL_NAME = MODEL_NAME


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


def safe_display_dataframe(df: pd.DataFrame, max_rows: int = 100, hide_index: bool = True) -> None:
    """Display a dataframe safely using pure HTML/CSS, eliminating PyArrow C-extension segfaults."""
    if df is None or df.empty:
        st.info("Empty table")
        return
    subset = df.head(max_rows)
    html_table = arrow_safe_preview(subset).to_html(index=not hide_index, escape=True)
    container_html = f"""
    <div style="max-height: 400px; overflow-y: auto; overflow-x: auto; border: 1px solid #2e384d; border-radius: 8px; margin-bottom: 15px;">
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: system-ui, -apple-system, sans-serif; font-size: 0.88rem; color: #e0e6ed; }}
            th {{ background-color: #1e2430; color: #4da6ff; position: sticky; top: 0; padding: 10px 12px; text-align: left; border-bottom: 2px solid #2e384d; font-weight: 600; }}
            td {{ padding: 8px 12px; border-bottom: 1px solid #2e384d; white-space: nowrap; }}
            tr:nth-child(even) {{ background-color: #161b26; }}
            tr:nth-child(odd) {{ background-color: #0e1117; }}
            tr:hover {{ background-color: #2b3548; }}
        </style>
        {html_table}
    </div>
    """
    st.markdown(container_html, unsafe_allow_html=True)


def _get_dataset_info(path: Path) -> dict:
    """Extract metadata, column statistics, and preview from the active SQLite database."""
    if not path.exists():
        return {"exists": False, "rows": 0, "columns": [], "df": pd.DataFrame(), "stats": pd.DataFrame()}
    
    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        table_name = tables[0][0] if tables else "sales"
        
        df_full = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
    rows, col_count = len(df_full), len(df_full.columns)
    
    # Calculate column stats
    stats = []
    for col in df_full.columns:
        series = df_full[col]
        null_count = series.isna().sum()
        unique_count = series.nunique()
        dtype_str = str(series.dtype)
        stats.append({
            "Column": str(col),
            "Type": str(dtype_str),
            "Non-Null": f"{rows - null_count:,} / {rows:,}",
            "Null Count": int(null_count),
            "Unique": int(unique_count),
            "Sample": str(series.dropna().iloc[0]) if not series.dropna().empty else "-"
        })
        
    return {
        "exists": True,
        "table_name": table_name,
        "rows": rows,
        "columns": list(df_full.columns),
        "df": df_full,
        "stats": pd.DataFrame(stats)
    }


def _extract_sql_queries(tool_results: list) -> list[str]:
    """Extract SQL query strings safely from agent tool results."""
    queries = []
    for item in tool_results:
        if isinstance(item, dict):
            query = item.get("query")
            if query and isinstance(query, str) and query not in queries:
                queries.append(query)
    return queries


def _set_preset_prompt(text: str) -> None:
    """Callback to update text area prompt input safely before page render."""
    st.session_state.prompt_input = text


def _generate_markdown_report(question: str, answer: str, sql_queries: list[str], dataset_name: str) -> str:
    """Generate a clean downloadable markdown report of the analysis."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = f"""# Executive Data Analysis Report
**Generated**: {timestamp}  
**Dataset**: `{dataset_name}`  

---

## ❓ Query
> {question}

---

## 💡 Executive Summary & Findings
{answer}

---

## 🛠️ Generated SQL Queries
"""
    if sql_queries:
        for idx, q in enumerate(sql_queries, start=1):
            report += f"\n### Query {idx}\n```sql\n{q}\n```\n"
    else:
        report += "\n*No direct SQL queries were captured for this result.*\n"

    report += "\n---\n*Report generated automatically by Agentic AI Data Analyst.*"
    return report


def _generate_html_report(question: str, answer: str, sql_queries: list[str], dataset_name: str) -> str:
    """Generate a self-contained HTML report with modern executive styling."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql_html = ""
    if sql_queries:
        for idx, q in enumerate(sql_queries, start=1):
            sql_html += f"<h4 style='color:#8b9bb4;margin-bottom:4px;'>Query #{idx}</h4><pre style='background:#1b222d;color:#50fa7b;padding:12px;border-radius:6px;overflow-x:auto;border:1px solid #2e384d;'>{q}</pre>"
    else:
        sql_html = "<p><em>No direct SQL queries captured for this result.</em></p>"

    # Basic markdown line-break conversion for HTML
    formatted_answer = answer.replace("\n", "<br>")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Executive Data Analysis Report - {dataset_name}</title>
<style>
body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0e1117; color: #e0e6ed; padding: 40px; line-height: 1.6; max-width: 960px; margin: 0 auto; }}
.header {{ border-bottom: 2px solid #2e384d; padding-bottom: 20px; margin-bottom: 30px; }}
.title {{ color: #4da6ff; margin: 0 0 12px 0; font-size: 1.8rem; }}
.badge {{ background-color: #2b3548; padding: 6px 12px; border-radius: 16px; font-size: 0.85rem; color: #a0aec0; border: 1px solid #3f4d67; margin-right: 8px; }}
.card {{ background-color: #161b26; border: 1px solid #2e384d; border-radius: 10px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
h2 {{ color: #4da6ff; margin-top: 0; font-size: 1.3rem; border-bottom: 1px solid #2e384d; padding-bottom: 8px; }}
blockquote {{ border-left: 4px solid #4da6ff; margin: 0; padding: 12px 18px; background-color: #1e2430; border-radius: 0 8px 8px 0; font-size: 1.05rem; }}
footer {{ text-align: center; margin-top: 40px; color: #718096; font-size: 0.85rem; border-top: 1px solid #2e384d; padding-top: 20px; }}
</style>
</head>
<body>
<div class="header">
  <h1 class="title">📊 Executive Data Analysis Report</h1>
  <span class="badge">📁 Dataset: {dataset_name}</span>
  <span class="badge">🕒 Generated: {timestamp}</span>
</div>
<div class="card">
  <h2>❓ Analysis Question</h2>
  <blockquote>{question}</blockquote>
</div>
<div class="card">
  <h2>💡 Key Insights & Findings</h2>
  <div>{formatted_answer}</div>
</div>
<div class="card">
  <h2>🛠️ Executed SQL Queries</h2>
  {sql_html}
</div>
<footer>Generated automatically by Agentic AI Data Analyst</footer>
</body>
</html>"""
    return html


def _set_active_history_item(item: dict) -> None:
    """Callback to reload a past history item into the active workspace."""
    st.session_state.current_result = item
    st.session_state.prompt_input = item["question"]


def _clear_session_history() -> None:
    """Callback to clear session history."""
    st.session_state.history = []


def main() -> None:
    st.set_page_config(
        page_title="Agentic AI Data Analyst Hub",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inject Custom CSS for premium styling
    st.markdown("""
        <style>
        .metric-card {
            background-color: #1e2430;
            border: 1px solid #2e384d;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
        }
        .metric-title {
            font-size: 0.8rem;
            color: #8b9bb4;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-value {
            font-size: 1.3rem;
            font-weight: 700;
            color: #4da6ff;
        }
        .preset-chip {
            background-color: #2b3548;
            color: #e0e6ed;
            border: 1px solid #3f4d67;
            border-radius: 16px;
            padding: 4px 12px;
            font-size: 0.85rem;
            margin-right: 6px;
            margin-bottom: 6px;
            display: inline-block;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize Session State
    if "database_path" not in st.session_state:
        st.session_state.database_path = PROJECT_ROOT / "database" / "sales.db"
    if "history" not in st.session_state:
        st.session_state.history = []
    if "prompt_input" not in st.session_state:
        st.session_state.prompt_input = ""

    _remove_expired_uploads(UPLOAD_DIR)
    db_path = Path(st.session_state.database_path)
    ds_info = _get_dataset_info(db_path)

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("📂 Dataset & Schema")
        upload = st.file_uploader("Upload CSV or Excel", type=["csv", "xls", "xlsx"])
        if upload and st.button("🚀 Load Dataset into Database", type="primary"):
            safe_name = "".join(char if char.isalnum() else "_" for char in Path(upload.name).stem)
            content = upload.getvalue()
            digest = sha256(content).hexdigest()[:12]
            target = UPLOAD_DIR / f"{safe_name}_{digest}_{uuid4().hex}.db"
            try:
                path, rows, columns = load_tabular_dataset(content, upload.name, target)
                st.session_state.database_path = path
                st.success(f"Loaded `{path.name}` ({rows:,} rows, {len(columns)} cols).")
                st.rerun()
            except (ValueError, pd.errors.ParserError) as error:
                st.error(str(error))
        
        if st.button("🔄 Reset to Bundled Sales Sample"):
            st.session_state.database_path = PROJECT_ROOT / "database" / "sales.db"
            st.rerun()

        st.divider()

        # Dataset Metadata Card
        if ds_info["exists"]:
            st.subheader("📊 Active Dataset Summary")
            st.caption(f"**Database**: `{db_path.name}`")
            col_s1, col_s2 = st.columns(2)
            col_s1.metric("Rows", f"{ds_info['rows']:,}")
            col_s2.metric("Columns", f"{len(ds_info['columns'])}")

            with st.expander("🔍 Schema Details & Types", expanded=False):
                safe_display_dataframe(
                    ds_info["stats"][["Column", "Type", "Non-Null", "Unique"]],
                    max_rows=100,
                    hide_index=True
                )

        st.divider()
        st.caption("🤖 **Engine**: LangGraph + Groq LLM")

    # --- MAIN PAGE HEADER ---
    st.title("📊 Agentic AI Data Analyst")
    st.caption("Autonomous data exploration, SQL reasoning, and automated visualization hub.")

    # Status Badges
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-title">Active Database</div><div class="metric-value">{db_path.name}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-title">Total Records</div><div class="metric-value">{ds_info["rows"]:,}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-title">Total Columns</div><div class="metric-value">{len(ds_info["columns"])}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-title">Model Engine</div><div class="metric-value">{DEFAULT_MODEL_NAME}</div></div>', unsafe_allow_html=True)

    st.subheader("What would you like to analyze?")

    # Preset Prompt Chips with on_click callbacks
    st.markdown("**Quick Preset Queries:**")
    cp1, cp2, cp3, cp4 = st.columns(4)
    cp1.button(
        "📈 Monthly Sales & Profit",
        on_click=_set_preset_prompt,
        args=("Analyze monthly sales and profit trends over time, then generate a chart.",),
        use_container_width=True
    )
    cp2.button(
        "🏆 Top 5 Customer Segments",
        on_click=_set_preset_prompt,
        args=("Who are the top 5 customers or segments by revenue? Create a visual bar chart.",),
        use_container_width=True
    )
    cp3.button(
        "📦 Category Profitability",
        on_click=_set_preset_prompt,
        args=("Compare overall revenue and profit margin across product categories.",),
        use_container_width=True
    )
    cp4.button(
        "🔍 Summary & Anomalies",
        on_click=_set_preset_prompt,
        args=("Provide a general statistical summary of key metrics and highlight any notable insights.",),
        use_container_width=True
    )

    question = st.text_area(
        "Analysis Query",
        key="prompt_input",
        placeholder="e.g. Compare monthly sales and profit, then create a bar chart.",
        height=90,
        label_visibility="collapsed"
    )

    ctrl_col1, ctrl_col2 = st.columns([3, 1])
    with ctrl_col1:
        refresh = st.checkbox("Bypass response cache & rerun analysis")
    with ctrl_col2:
        run_analysis = st.button("🚀 Run Analysis", type="primary", use_container_width=True, disabled=not question.strip())

    # --- AGENT EXECUTION ---
    if run_analysis:
        set_database_path(st.session_state.database_path)
        dataset_id = active_dataset_id()
        cached = None if refresh else response_cache.get(dataset_id, question)

        if cached:
            st.info("⚡ Returned cached response for this dataset & query. Check 'Bypass cache' to force rerun.")
            answer, artifacts, trace, tool_results = (
                cached["answer"], cached.get("artifacts", []), cached.get("trace", []), cached.get("tool_results", []),
            )
        else:
            with st.status("🧠 Planning, querying SQL database, validating & generating insights...", expanded=True) as status:
                try:
                    result = graph.invoke({"messages": [HumanMessage(content=question)], "trace": []}, config={"recursion_limit": 100})
                    status.update(label="✅ Analysis Complete!", state="complete")
                except Exception as error:
                    status.update(label="❌ Analysis Failed", state="error")
                    if "rate_limit" in str(error).lower() or "rate limit" in str(error).lower():
                        st.warning("Groq API rate limit reached. Please wait a moment and try again.")
                    st.error(f"Error details: {error}")
                    return

            answer = str(result["messages"][-1].content)
            artifacts = [artifact.model_dump() for artifact in result.get("artifacts", [])]
            trace = result.get("trace", [])
            tool_results = [item.result or {"tool": item.tool, "message": item.message} for item in result.get("tool_results", [])]
            response_cache.put(dataset_id, question, {"answer": answer, "artifacts": artifacts, "trace": trace, "tool_results": tool_results})

        # Save to session history
        sql_queries = _extract_sql_queries(tool_results)
        item_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "question": question,
            "answer": answer,
            "artifacts": artifacts,
            "trace": trace,
            "tool_results": tool_results,
            "sql_queries": sql_queries
        }
        st.session_state.history.append(item_entry)
        st.session_state.current_result = item_entry

    # --- RESULTS MULTI-TAB WORKSPACE ---
    if "current_result" in st.session_state:
        res = st.session_state.current_result
        st.divider()

        tab_brief, tab_explorer, tab_reasoning, tab_export = st.tabs([
            "💡 Executive Brief & Visuals",
            "📊 Data Explorer",
            "🛠️ Agent Reasoning & SQL",
            "📜 History & Export Report"
        ])

        # TAB 1: EXECUTIVE BRIEF & VISUALS
        with tab_brief:
            st.markdown("### Executive Summary")
            st.markdown(res["answer"])

            # Render Generated Charts
            charts = [art for art in res["artifacts"] if art.get("type") == "CHART"]
            if charts:
                st.markdown("---")
                st.markdown("### 📈 Visualizations")
                c_cols = st.columns(len(charts) if len(charts) <= 2 else 2)
                for idx, artifact in enumerate(charts):
                    chart_rel_path = artifact.get("payload", {}).get("chart_path", "")
                    chart_full_path = PROJECT_ROOT / chart_rel_path
                    title = artifact.get("payload", {}).get("title", f"Chart {idx+1}")
                    target_col = c_cols[idx % len(c_cols)]
                    with target_col:
                        if chart_full_path.is_file():
                            st.image(str(chart_full_path), caption=title, use_container_width=True)
                            with open(chart_full_path, "rb") as file:
                                st.download_button(
                                    label=f"💾 Download {title}.png",
                                    data=file,
                                    file_name=f"{Path(chart_rel_path).name}",
                                    mime="image/png",
                                    key=f"dl_chart_{idx}"
                                )

        # TAB 2: INTERACTIVE DATA EXPLORER
        with tab_explorer:
            st.markdown("### 📊 Active Dataset Explorer")
            if ds_info["exists"] and not ds_info["df"].empty:
                st.caption(f"Showing dataset: `{db_path.name}` ({ds_info['rows']:,} rows × {len(ds_info['columns'])} columns)")
                
                # Search filter
                search_term = st.text_input("🔍 Filter rows by keyword:", placeholder="Type to search across dataset...")
                df_display = ds_info["df"]
                if search_term:
                    mask = df_display.astype(str).apply(lambda row: row.str.contains(search_term, case=False).any(), axis=1)
                    df_display = df_display[mask]
                    st.caption(f"Found {len(df_display):,} matching rows.")

                # Arrow-safe table preview
                safe_display_dataframe(df_display, max_rows=100, hide_index=True)
                if len(df_display) > 100:
                    st.caption("*Displaying first 100 preview rows.*")

                st.markdown("#### 📋 Column Profiling & Null Breakdown")
                safe_display_dataframe(ds_info["stats"], max_rows=100, hide_index=True)
            else:
                st.info("No dataset is currently loaded.")

        # TAB 3: AGENT REASONING & SQL INSPECTOR
        with tab_reasoning:
            st.markdown("### 🛠️ Agent Execution & SQL Inspector")
            
            # SQL Queries Section
            if res["sql_queries"]:
                st.markdown("#### ⚡ Executed SQL Queries")
                for q_idx, query in enumerate(res["sql_queries"], start=1):
                    st.markdown(f"**Query #{q_idx}:**")
                    st.code(query, language="sql")
            else:
                st.info("No SQL queries were executed during this prompt.")

            st.markdown("---")
            st.markdown("#### 📜 Agent Step Trace")
            with st.expander("View detailed execution step trace", expanded=True):
                st.code("\n".join(res["trace"]) if res["trace"] else "No trace recorded.", language="text")

            st.markdown("#### 🔧 Raw Tool Results")
            with st.expander("View structured tool call outputs (JSON)", expanded=False):
                st.json(res["tool_results"])

        # TAB 4: USER-FRIENDLY HISTORY & EXPORT REPORT
        with tab_export:
            st.markdown("### 📜 Session History & One-Click Export")
            st.caption("Download reports in multiple formats or reload any past analysis from this session.")

            # --- EXPORT BUTTONS ROW ---
            st.markdown("#### 📥 Export Active Analysis")
            report_md = _generate_markdown_report(
                question=res["question"],
                answer=res["answer"],
                sql_queries=res["sql_queries"],
                dataset_name=db_path.name
            )
            report_html = _generate_html_report(
                question=res["question"],
                answer=res["answer"],
                sql_queries=res["sql_queries"],
                dataset_name=db_path.name
            )
            sql_text = "\n\n".join(res["sql_queries"]) if res["sql_queries"] else "-- No SQL queries captured"

            exp_col1, exp_col2, exp_col3 = st.columns(3)
            with exp_col1:
                st.download_button(
                    label="📄 Download Markdown (.md)",
                    data=report_md,
                    file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    type="primary"
                )
            with exp_col2:
                st.download_button(
                    label="🌐 Download Web Report (.html)",
                    data=report_html,
                    file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html",
                    use_container_width=True
                )
            with exp_col3:
                st.download_button(
                    label="⚡ Download SQL Queries (.sql)",
                    data=sql_text,
                    file_name=f"queries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                    mime="text/plain",
                    use_container_width=True
                )

            st.divider()

            # --- SESSION HISTORY METRICS & TIMELINE ---
            h_head_col1, h_head_col2 = st.columns([3, 1])
            with h_head_col1:
                st.markdown(f"#### 🕓 Session History Log ({len(st.session_state.history)} queries)")
            with h_head_col2:
                if st.session_state.history:
                    st.button("🗑️ Clear History", on_click=_clear_session_history, use_container_width=True)

            if st.session_state.history:
                for item_idx, item in enumerate(reversed(st.session_state.history), start=1):
                    # Card container for each history entry
                    with st.expander(
                        f"🕒 [{item['timestamp']}] {item['question']}",
                        expanded=(item_idx == 1)
                    ):
                        st.markdown(f"**Query**: {item['question']}")
                        st.markdown("**Executive Answer Preview:**")
                        st.markdown(item["answer"])
                        
                        if item["sql_queries"]:
                            st.caption(f"⚡ {len(item['sql_queries'])} SQL query executed:")
                            for q in item["sql_queries"]:
                                st.code(q, language="sql")
                        
                        # Reload into workspace button
                        st.button(
                            "🔄 Load this Analysis into Workspace",
                            key=f"reload_hist_{item_idx}",
                            on_click=_set_active_history_item,
                            args=(item,),
                            type="secondary"
                        )
            else:
                st.info("No prior queries recorded in this session. Run your first query above to build history!")


if __name__ == "__main__":
    main()


