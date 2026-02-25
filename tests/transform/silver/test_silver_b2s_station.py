from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.connection.db import get_connection
from src.transform.silver.B2S_station import (
    create_silver_station,
    upsert_silver_station_from_bronze,
)


def _create_bronze_station(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bronze_station (
            station_id   TEXT PRIMARY KEY,
            label        TEXT,
            river_name   TEXT,
            lat          REAL,
            long         REAL,
            easting      INTEGER,
            northing     INTEGER,
            status       TEXT,
            ingested_at  TEXT NOT NULL
        )
    """)
    conn.commit()


def test_create_silver_station_creates_table(tmp_path: Path):
    conn = get_connection(str(tmp_path / "s.db"))
    create_silver_station(conn)

    row = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='silver_station'
    """).fetchone()

    conn.close()
    assert row is not None


def test_upsert_silver_station_from_bronze_upserts_latest_batch(tmp_path: Path):
    conn = get_connection(str(tmp_path / "s2.db"))
    _create_bronze_station(conn)
    create_silver_station(conn)

    ts = "2026-02-25T00:00:00+00:00"

    conn.execute("""
        INSERT INTO bronze_station(station_id, label, river_name, lat, long, ingested_at)
        VALUES ('E64999A', 'NAME V1', 'HIPPER', 53.2, -1.4, ?)
    """, (ts,))
    conn.commit()

    count = upsert_silver_station_from_bronze(conn, ts)
    assert count >= 1

    r = conn.execute("""
        SELECT station_id, label, river_name, ingested_at
        FROM silver_station WHERE station_id='E64999A'
    """).fetchone()

    conn.close()

    assert r["label"] == "NAME V1"
    assert r["river_name"] == "HIPPER"
    assert r["ingested_at"] == ts