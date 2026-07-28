"""Safe local dataset ingestion for the web dashboard."""

import re
import sqlite3
from io import BytesIO
from pathlib import Path

import pandas as pd


def _column_name(value: str, index: int) -> str:
    name = re.sub(r"[^a-z0-9_]+", "_", str(value).strip().lower()).strip("_")
    return name or f"column_{index}"


def load_tabular_dataset(content: bytes, filename: str, destination: str | Path) -> tuple[Path, int, list[str]]:
    """Load a CSV or Excel upload into a new SQLite ``sales`` table."""
    suffix = Path(filename).suffix.lower()
    stream = BytesIO(content)
    if suffix == ".csv":
        frame = pd.read_csv(stream)
    elif suffix in {".xlsx", ".xls"}:
        frame = pd.read_excel(stream)
    else:
        raise ValueError("Upload a CSV, XLS, or XLSX file.")
    if frame.empty:
        raise ValueError("The uploaded dataset has no rows.")
    columns, seen = [], set()
    for index, column in enumerate(frame.columns, start=1):
        base, candidate, suffix_index = _column_name(column, index), "", 1
        candidate = base
        while candidate in seen:
            suffix_index += 1
            candidate = f"{base}_{suffix_index}"
        seen.add(candidate); columns.append(candidate)
    frame.columns = columns
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    with sqlite3.connect(target) as connection:
        frame.to_sql("sales", connection, index=False, if_exists="replace")
    return target, len(frame), columns


def arrow_safe_preview(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize mixed object columns before passing a frame to Streamlit."""
    preview = frame.copy()
    for column in preview.select_dtypes(include="object").columns:
        values = preview[column]
        non_empty = values.replace(r"^\s*$", pd.NA, regex=True)
        numeric = pd.to_numeric(non_empty, errors="coerce")
        # Retain a numeric dtype only when every meaningful value is numeric.
        if non_empty.notna().sum() == numeric.notna().sum():
            preview[column] = numeric
        else:
            preview[column] = values.astype("string").fillna("")
    return preview
