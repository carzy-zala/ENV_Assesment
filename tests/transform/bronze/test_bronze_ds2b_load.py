from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.connection.db import get_connection, init_raw_table, insert_raw_payload
from src.load.DS2B_load import run_ds2b


def test_run_ds2b_processes_latest_ingestion_only(tmp_path: Path):
    conn = get_connection(str(tmp_path / "ds2b.db"))
    init_raw_table(conn)

    # Insert older ingestion run
    old_ts = "2026-02-24T00:00:00Z"
    station_payload_old = {"items": [{"notation": "E64999A", "label": "OLD NAME"}]}
    insert_raw_payload(conn, "station_search", json.dumps(station_payload_old), ingested_at=old_ts)

    old_readings = {"items": [{"dateTime": "2026-02-24T00:00:00Z", "value": 0.1}]}
    insert_raw_payload(
        conn,
        "readings_latest__dissolved_oxygen__E64999A-do-i-subdaily-mgL",
        json.dumps(old_readings),
        ingested_at=old_ts,
    )

    # Insert latest ingestion run
    new_ts = "2026-02-25T00:00:00Z"
    station_payload_new = {"items": [{"notation": "E64999A", "label": "NEW NAME"}]}
    insert_raw_payload(conn, "station_search", json.dumps(station_payload_new), ingested_at=new_ts)

    new_do = {"items": [{"dateTime": "2026-02-25T00:00:00Z", "value": 1.23}]}
    new_cond = {"items": [{"dateTime": "2026-02-25T00:00:00Z", "value": 200.0}]}
    insert_raw_payload(
        conn,
        "readings_latest__dissolved_oxygen__E64999A-do-i-subdaily-mgL",
        json.dumps(new_do),
        ingested_at=new_ts,
    )
    insert_raw_payload(
        conn,
        "readings_latest__conductivity__E64999A-cond-i-subdaily-uS",
        json.dumps(new_cond),
        ingested_at=new_ts,
    )

    summary = run_ds2b(conn)
    assert summary["status"] == "ok"
    assert summary["ingested_at"] == new_ts

    # bronze_station should reflect NEW NAME (latest run)
    s = conn.execute("SELECT station_id, label, ingested_at FROM bronze_station WHERE station_id='E64999A'").fetchone()
    assert s["label"] == "NEW NAME"
    assert s["ingested_at"] == new_ts

    # bronze_measure should contain ONLY latest run's readings (2 rows)
    m_count = conn.execute("SELECT COUNT(*) FROM bronze_measure WHERE ingested_at = ?", (new_ts,)).fetchone()[0]
    assert m_count == 2

    # Ensure older run not included in bronze_measure latest filter logic
    old_count = conn.execute("SELECT COUNT(*) FROM bronze_measure WHERE ingested_at = ?", (old_ts,)).fetchone()[0]
    assert old_count == 0

    conn.close()