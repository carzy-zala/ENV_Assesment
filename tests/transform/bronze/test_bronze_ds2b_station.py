from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.connection.db import get_connection, init_raw_table
from src.transform.bronze.DS2B_station import (
    create_bronze_station_table,
    station_rows_from_payload,
    upsert_bronze_station,
)


def test_station_rows_from_payload_extracts_items(tmp_path: Path):
    conn = get_connection(str(tmp_path / "s.db"))
    create_bronze_station_table(conn)

    payload = {
        "items": [
            {
                "notation": "E64999A",
                "label": "HIPPER_PARK ROAD BRIDGE_E_202312",
                "riverName": "HIPPER",
                "lat": 53.234837,
                "long": -1.437039,
                "easting": 437673,
                "northing": 371016,
                "status": [{"label": "Active"}],
            }
        ]
    }

    rows = station_rows_from_payload(payload, ingested_at="2026-02-25T00:00:00Z")
    assert len(rows) == 1
    assert rows[0]["station_id"] == "E64999A"
    assert rows[0]["label"].startswith("HIPPER")
    assert rows[0]["status"] == "Active"

    conn.close()


def test_upsert_bronze_station_inserts_and_updates(tmp_path: Path):
    conn = get_connection(str(tmp_path / "s2.db"))
    create_bronze_station_table(conn)

    payload_v1 = {
        "items": [{"notation": "E64999A", "label": "NAME V1", "riverName": "R1", "lat": 1.0, "long": 2.0}]
    }
    rows_v1 = station_rows_from_payload(payload_v1, ingested_at="2026-02-25T00:00:00Z")
    upsert_bronze_station(conn, rows_v1)

    r1 = conn.execute("SELECT station_id, label, ingested_at FROM bronze_station WHERE station_id='E64999A'").fetchone()
    assert r1["label"] == "NAME V1"
    assert r1["ingested_at"] == "2026-02-25T00:00:00Z"

    payload_v2 = {
        "items": [{"notation": "E64999A", "label": "NAME V2", "riverName": "R2", "lat": 3.0, "long": 4.0}]
    }
    rows_v2 = station_rows_from_payload(payload_v2, ingested_at="2026-02-26T00:00:00Z")
    upsert_bronze_station(conn, rows_v2)

    r2 = conn.execute("SELECT station_id, label, river_name, ingested_at FROM bronze_station WHERE station_id='E64999A'").fetchone()
    assert r2["label"] == "NAME V2"
    assert r2["river_name"] == "R2"
    assert r2["ingested_at"] == "2026-02-26T00:00:00Z"

    conn.close()