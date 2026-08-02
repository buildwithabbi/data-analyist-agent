from data_analyst_agent.tools import active_dataset_id, set_database_path
from data_analyst_agent.tools.analytics import DB_PATH


def test_dataset_fingerprint_changes_with_database_content(tmp_path):
    first = tmp_path / "first.db"
    second = tmp_path / "second.db"
    first.write_bytes(b"first database")
    second.write_bytes(b"second database")

    try:
        set_database_path(first)
        first_id = active_dataset_id()
        set_database_path(second)
        second_id = active_dataset_id()
    finally:
        set_database_path(DB_PATH)

    assert first_id.startswith("sha256:")
    assert first_id != second_id
