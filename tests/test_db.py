from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.connection.db import (
    get_connection,
    init_raw_table,
    insert_raw_payload,
)


def test_get_connection_creates_db_file(tmp_path: Path):
    db_path = tmp_path / "my_test.db"

    conn = get_connection(str(db_path))
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")
    conn.commit()
    conn.close()

    assert db_path.exists()


def test_get_connection_enables_foreign_keys(tmp_path: Path):
    db_path = tmp_path / "fk_test.db"
    conn = get_connection(str(db_path))

    fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
    conn.close()

    assert fk == 1


def test_init_raw_table_creates_table(tmp_path: Path):
    db_path = tmp_path / "raw_test.db"
    conn = get_connection(str(db_path))

    init_raw_table(conn)

    # check table exists
    row = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='raw_landing'
    """).fetchone()

    conn.close()

    assert row is not None
    assert row["name"] == "raw_landing"


def test_insert_raw_payload_stores_json(tmp_path: Path):
    db_path = tmp_path / "insert_test.db"
    conn = get_connection(str(db_path))
    init_raw_table(conn)

    sample_payload = {"hello": "world", "value": 42}
    insert_raw_payload(conn, "test_dataset", json.dumps(sample_payload))

    row = conn.execute("SELECT dataset, payload FROM raw_landing").fetchone()
    conn.close()

    assert row is not None
    assert row["dataset"] == "test_dataset"

    stored = json.loads(row["payload"])
    assert stored == sample_payload