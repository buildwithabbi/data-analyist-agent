"""Safe local dataset ingestion for the web dashboard."""

import re
import sqlite3
import os
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

import pandas as pd


MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_DATASET_ROWS = 500_000
MAX_DATASET_COLUMNS = 200
MAX_EXCEL_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_EXCEL_ARCHIVE_MEMBERS = 500


def _column_name(value: str, index: int) -> str:
    name = re.sub(r"[^a-z0-9_]+", "_", str(value).strip().lower()).strip("_")
    return name or f"column_{index}"


def _validate_excel_archive(content: bytes) -> None:
    """Reject XLSX archives that would expand beyond local resource limits."""
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            members = archive.infolist()
            if len(members) > MAX_EXCEL_ARCHIVE_MEMBERS:
                raise ValueError("The Excel file has too many archive entries.")
            if sum(member.file_size for member in members) > MAX_EXCEL_UNCOMPRESSED_BYTES:
                raise ValueError("The Excel file expands beyond the 100 MB limit.")
    except zipfile.BadZipFile as error:
        raise ValueError("The XLSX upload is not a valid Excel archive.") from error


def load_tabular_dataset(content: bytes, filename: str, destination: str | Path) -> tuple[Path, int, list[str]]:
    """Load a CSV or Excel upload into a new SQLite ``sales`` table."""
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("The upload exceeds the 20 MB limit.")
    suffix = Path(filename).suffix.lower()
    stream = BytesIO(content)
    if suffix == ".csv":
        frame = pd.read_csv(stream)
    elif suffix in {".xlsx", ".xls"}:
        if suffix == ".xlsx":
            _validate_excel_archive(content)
        frame = pd.read_excel(stream)
    else:
        raise ValueError("Upload a CSV, XLS, or XLSX file.")
    if frame.empty:
        raise ValueError("The uploaded dataset has no rows.")
    if len(frame) > MAX_DATASET_ROWS:
        raise ValueError(f"The dataset exceeds the {MAX_DATASET_ROWS:,}-row limit.")
    if len(frame.columns) > MAX_DATASET_COLUMNS:
        raise ValueError(f"The dataset exceeds the {MAX_DATASET_COLUMNS}-column limit.")
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
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.stem}_", suffix=".db", dir=target.parent)
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        with sqlite3.connect(temporary_path) as connection:
            frame.to_sql("sales", connection, index=False, if_exists="replace")
        os.replace(temporary_path, target)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return target, len(frame), columns


def arrow_safe_preview(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize mixed object columns before passing a frame to Streamlit."""
    preview = frame.copy()
    for column in preview.select_dtypes(include="object").columns:
        values = preview[column]
        non_empty = values.replace(r"^\s*$", pd.NA, regex=True).infer_objects(copy=False)
        numeric = pd.to_numeric(non_empty, errors="coerce")
        # Retain a numeric dtype only when every meaningful value is numeric.
        if non_empty.notna().sum() == numeric.notna().sum():
            preview[column] = numeric
        else:
            preview[column] = values.astype("string").fillna("")
    return preview
