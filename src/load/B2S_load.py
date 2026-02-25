import sqlite3
from typing import Dict, Any

from src.transform.silver.B2S_station import create_silver_station, upsert_silver_station_from_bronze
from src.transform.silver.B2S_measure import create_silver_measure, insert_silver_measure_from_bronze


def run_b2s(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Bronze -> Silver for latest ingested_at.
    """
    create_silver_station(conn)
    create_silver_measure(conn)

    latest_ingested_at = conn.execute("SELECT MAX(ingested_at) FROM raw_landing").fetchone()[0]
    if not latest_ingested_at:
        return {"status": "no_raw_data"}

    station_upserts = upsert_silver_station_from_bronze(conn, latest_ingested_at)
    measure_inserts = insert_silver_measure_from_bronze(conn, latest_ingested_at)

    return {
        "status": "ok",
        "ingested_at": latest_ingested_at,
        "silver_station_upserts": station_upserts,
        "silver_measure_inserts": measure_inserts,
    }