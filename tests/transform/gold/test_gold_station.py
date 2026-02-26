from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from utils.connection.db import get_connection
from src.transform.gold.S2G_station import create_fact_station, upsert_fact_station_from_silver


def _create_silver_station(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS silver_station (
            station_id  TEXT PRIMARY KEY,
            label       TEXT,
            river_name  TEXT,
            lat         REAL,
            long        REAL,
            easting     INTEGER,
            northing    INTEGER,
            status      TEXT,
            ingested_at TEXT NOT NULL
        )
    """)
    conn.commit()


def test_create_fact_station_creates_table(tmp_path: Path):
    conn = get_connection(str(tmp_path / "g_station_1.db"))
    create_fact_station(conn)

    row = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='fact_station'
    """).fetchone()

    conn.close()
    assert row is not None


def test_upsert_fact_station_from_silver_upserts(tmp_path: Path):
    conn = get_connection(str(tmp_path / "g_station_2.db"))
    _create_silver_station(conn)
    create_fact_station(conn)

    ts = "2026-02-25T00:00:00+00:00"

    conn.execute("""
        INSERT INTO silver_station(station_id,label,river_name,lat,long,ingested_at)
        VALUES ('E64999A','HIPPER_PARK ROAD BRIDGE_E_202312','HIPPER',53.2,-1.4,?)
    """, (ts,))
    conn.commit()

    upsert_fact_station_from_silver(conn, ts)

    r = conn.execute("""
        SELECT station_id, label, river_name, ingested_at
        FROM fact_station WHERE station_id='E64999A'
    """).fetchone()

    conn.close()

    assert r["station_id"] == "E64999A"
    assert r["label"].startswith("HIPPER")
    assert r["river_name"] == "HIPPER"
    assert r["ingested_at"] == ts