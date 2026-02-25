import json
import sqlite3
from typing import Dict, Any

from src.transform.bronze.DS2B_station import (
    create_bronze_station_table,
    station_rows_from_payload,
    upsert_bronze_station,
)

from src.transform.bronze.DS2B_measure import (
    create_bronze_measure_table,
    measure_rows_from_payload,
    insert_bronze_measures,
)


def run_ds2b(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    DS2B: raw_landing -> bronze_station + bronze_measure
    Processes only the latest ingested_at batch to avoid duplicates on reruns.
    """
    create_bronze_station_table(conn)
    create_bronze_measure_table(conn)

    latest_ingested_at = conn.execute("""
        SELECT MAX(ingested_at) FROM raw_landing
    """).fetchone()[0]

    if not latest_ingested_at:
        return {"status": "no_raw_data"}

    raw_rows = conn.execute("""
        SELECT dataset, payload, ingested_at
        FROM raw_landing
        WHERE ingested_at = ?
        ORDER BY id
    """, (latest_ingested_at,)).fetchall()

    station_upserts = 0
    measure_inserts = 0

    for rr in raw_rows:
        dataset = rr["dataset"]
        payload = json.loads(rr["payload"])
        ingested_at = rr["ingested_at"]

        if dataset == "station_search":
            s_rows = station_rows_from_payload(payload, ingested_at)
            station_upserts += upsert_bronze_station(conn, s_rows)

        elif dataset.startswith("readings_latest__"):
            m_rows = measure_rows_from_payload(dataset, payload, ingested_at)
            measure_inserts += insert_bronze_measures(conn, m_rows)

    return {
        "status": "ok",
        "ingested_at": latest_ingested_at,
        "station_upserts": station_upserts,
        "measure_inserts": measure_inserts,
    }