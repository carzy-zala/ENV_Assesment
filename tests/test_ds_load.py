from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from unittest.mock import Mock

from utils.connection.db import get_connection, init_raw_table
from src.load.ds_load import extract_and_load_ds


def test_extract_and_load_bronze_inserts_station_and_all_readings(tmp_path: Path):
    db_path = tmp_path / "bronze_test.db"
    conn = get_connection(str(db_path))
    init_raw_table(conn)

    # Mock API responses:
    # 1) station payload
    # 2) readings for DO mgL
    # 3) readings for DO pct
    # 4) readings for conductivity
    station_payload = {
        "meta": {},
        "items": [{
            "label": "HIPPER_PARK ROAD BRIDGE_E_202312",
            "notation": "E64999A",
            "observedProperty": [
                {"@id": "http://environment.data.gov.uk/reference/def/op/dissolved-oxygen"},
                {"@id": "http://environment.data.gov.uk/reference/def/op/conductivity"},
            ],
            "measures": [
                {"@id": "http://environment.data.gov.uk/hydrology/id/measures/E64999A-do-i-subdaily-mgL", "parameter": "DISSOLVED OXYGEN"},
                {"@id": "http://environment.data.gov.uk/hydrology/id/measures/E64999A-do-i-subdaily-pct", "parameter": "DISSOLVED OXYGEN"},
                {"@id": "http://environment.data.gov.uk/hydrology/id/measures/E64999A-cond-i-subdaily-uS", "parameter": "CONDUCTIVITY"},
            ],
        }]
    }

    do_mgL_payload = {"items": [{"dateTime": "2026-02-25T00:00:00Z", "value": 1.0}]}
    do_pct_payload = {"items": [{"dateTime": "2026-02-25T00:00:00Z", "value": 99.0}]}
    cond_payload   = {"items": [{"dateTime": "2026-02-25T00:00:00Z", "value": 200.0}]}

    client = Mock()
    client.get_json.side_effect = [station_payload, do_mgL_payload, do_pct_payload, cond_payload]

    summary = extract_and_load_ds(
        conn=conn,
        client=client,
        station_ref="HIPPER_PARK ROAD BRIDGE_E_202312",
        requested_params=["dissolved oxygen", "conductivity"],
        limit=10,
    )

    rows = conn.execute("SELECT dataset, payload FROM raw_landing ORDER BY id").fetchall()
    conn.close()

    # Expect: 1 station row + 3 readings rows = 4
    assert len(rows) == 4
    assert rows[0]["dataset"] == "station_search"

    # Ensure all payloads are valid JSON
    for r in rows:
        json.loads(r["payload"])

    # Summary sanity
    assert summary["raw_rows_inserted"] == 4