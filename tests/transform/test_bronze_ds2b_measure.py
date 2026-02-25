from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.connection.db import get_connection
from src.transform.bronze.DS2B_measure import (
    create_bronze_measure_table,
    measure_rows_from_payload,
    insert_bronze_measures,
)


def test_measure_rows_from_payload_parses_dataset_and_rows(tmp_path: Path):
    conn = get_connection(str(tmp_path / "m.db"))
    create_bronze_measure_table(conn)

    dataset = "readings_latest__dissolved_oxygen__E64999A-do-i-subdaily-mgL"
    payload = {"items": [{"dateTime": "2026-02-25T00:00:00Z", "value": 1.23, "quality": "Good"}]}

    rows = measure_rows_from_payload(dataset, payload, ingested_at="2026-02-25T01:00:00Z")
    assert len(rows) == 1
    assert rows[0]["station_id"] == "E64999A"
    assert rows[0]["parameter"] == "dissolved oxygen"
    assert rows[0]["unit"] == "mgL"
    assert rows[0]["measure_id"].endswith("mgL")
    assert rows[0]["datetime"] == "2026-02-25T00:00:00Z"

    conn.close()


def test_insert_bronze_measures_inserts_rows(tmp_path: Path):
    conn = get_connection(str(tmp_path / "m2.db"))
    create_bronze_measure_table(conn)

    rows = [
        {
            "station_id": "E64999A",
            "parameter": "dissolved oxygen",
            "unit": "mgL",
            "measure_id": "E64999A-do-i-subdaily-mgL",
            "datetime": "2026-02-25T00:00:00Z",
            "value": 1.23,
            "quality": "Good",
            "completeness": "Complete",
            "ingested_at": "2026-02-25T01:00:00Z",
        },
        {
            "station_id": "E64999A",
            "parameter": "dissolved oxygen",
            "unit": "pct",
            "measure_id": "E64999A-do-i-subdaily-pct",
            "datetime": "2026-02-25T00:00:00Z",
            "value": 98.0,
            "quality": "Good",
            "completeness": "Complete",
            "ingested_at": "2026-02-25T01:00:00Z",
        },
    ]

    inserted = insert_bronze_measures(conn, rows)
    assert inserted == 2

    count = conn.execute("SELECT COUNT(*) FROM bronze_measure").fetchone()[0]
    assert count == 2

    conn.close()