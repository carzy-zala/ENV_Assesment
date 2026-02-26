import sqlite3
from typing import Dict, Any

from src.transform.gold.S2G_station import create_fact_station, upsert_fact_station_from_silver
from src.transform.gold.S2G_measure import create_dim_measurement, insert_dim_measurement_from_silver


def run_s2g(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Silver -> Gold for latest ingested_at (from raw_landing).
    """
    create_fact_station(conn)
    create_dim_measurement(conn)

    latest_ingested_at = conn.execute("SELECT MAX(ingested_at) FROM raw_landing").fetchone()[0]
    if not latest_ingested_at:
        return {"status": "no_raw_data"}

    dim_upserts = upsert_fact_station_from_silver(conn, latest_ingested_at)
    fact_inserts = insert_dim_measurement_from_silver(conn, latest_ingested_at)

    return {
        "status": "ok",
        "ingested_at": latest_ingested_at,
        "dim_station_upserts": dim_upserts,
        "fact_measurement_inserts": fact_inserts,
    }