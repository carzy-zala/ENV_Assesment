from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from utils.connection.db import get_connection
from src.load.S2G_load import run_s2g


def _create_raw_landing(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_landing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset TEXT NOT NULL,
            payload TEXT NOT NULL,
            ingested_at TEXT NOT NULL
        )
    """)
    conn.commit()


def _create_silver_tables(conn):
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS silver_measure (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id    TEXT NOT NULL,
            parameter     TEXT NOT NULL,
            unit          TEXT NOT NULL,
            measure_id    TEXT NOT NULL,
            datetime      TEXT NOT NULL,
            value         REAL,
            quality       TEXT,
            completeness  TEXT,
            ingested_at   TEXT NOT NULL,
            UNIQUE(measure_id, datetime, ingested_at)
        )
    """)
    conn.commit()


def test_run_s2g_builds_dim_and_fact(tmp_path: Path):
    conn = get_connection(str(tmp_path / "g.db"))
    _create_raw_landing(conn)
    _create_silver_tables(conn)

    ts = "2026-02-25T00:00:00+00:00"

    # latest ingested_at comes from raw_landing
    conn.execute("INSERT INTO raw_landing(dataset,payload,ingested_at) VALUES ('station_search','{}',?)", (ts,))

    # silver input
    conn.execute("""
        INSERT INTO silver_station(station_id,label,ingested_at)
        VALUES ('E64999A','HIPPER_PARK ROAD BRIDGE_E_202312',?)
    """, (ts,))
    conn.execute("""
        INSERT INTO silver_measure(station_id,parameter,unit,measure_id,datetime,value,ingested_at)
        VALUES ('E64999A','dissolved oxygen','mgL','E64999A-do-i-subdaily-mgL','2026-02-25T00:00:00+00:00',1.0,?)
    """, (ts,))
    conn.commit()

    summary = run_s2g(conn)
    assert summary["status"] == "ok"
    assert summary["ingested_at"] == ts

    dim = conn.execute("SELECT COUNT(*) FROM dim_station").fetchone()[0]
    fact = conn.execute("SELECT COUNT(*) FROM fact_measurement").fetchone()[0]
    assert dim == 1
    assert fact == 1

    # joined key exists
    station_key = conn.execute("SELECT station_key FROM fact_measurement").fetchone()[0]
    assert station_key is not None

    conn.close()