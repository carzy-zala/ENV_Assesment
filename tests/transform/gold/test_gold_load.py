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


def test_run_s2g_builds_gold_from_latest_ingested_at(tmp_path: Path):
    conn = get_connection(str(tmp_path / "g_load.db"))
    _create_raw_landing(conn)
    _create_silver_tables(conn)

    old_ts = "2026-02-24T00:00:00+00:00"
    new_ts = "2026-02-25T00:00:00+00:00"

    # raw_landing drives "latest ingested_at"
    conn.execute("INSERT INTO raw_landing(dataset,payload,ingested_at) VALUES ('x','{}',?)", (old_ts,))
    conn.execute("INSERT INTO raw_landing(dataset,payload,ingested_at) VALUES ('x','{}',?)", (new_ts,))
    conn.commit()

    # seed silver for BOTH ingestions, but gold should load only new_ts
    conn.execute("""
        INSERT INTO silver_station(station_id,label,ingested_at)
        VALUES ('E64999A','OLD',?)
    """, (old_ts,))
    conn.execute("""
        INSERT OR REPLACE INTO silver_station(station_id,label,ingested_at)
        VALUES ('E64999A','NEW',?)
    """, (new_ts,))

    conn.execute("""
        INSERT INTO silver_measure(station_id,parameter,unit,measure_id,datetime,value,ingested_at)
        VALUES ('E64999A','dissolved oxygen','mgL','E64999A-do-i-subdaily-mgL','2026-02-25T00:00:00+00:00',1.0,?)
    """, (new_ts,))
    conn.commit()

    summary = run_s2g(conn)
    assert summary["status"] == "ok"
    assert summary["ingested_at"] == new_ts

    dim = conn.execute("SELECT COUNT(*) FROM fact_station").fetchone()[0]
    fact_new = conn.execute("SELECT COUNT(*) FROM dim_measurement WHERE ingested_at=?", (new_ts,)).fetchone()[0]
    fact_old = conn.execute("SELECT COUNT(*) FROM dim_measurement WHERE ingested_at=?", (old_ts,)).fetchone()[0]

    # station label should be NEW
    label = conn.execute("SELECT label FROM fact_station WHERE station_id='E64999A'").fetchone()[0]

    conn.close()

    assert dim == 1
    assert label == "NEW"
    assert fact_new == 1
    assert fact_old == 0