from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.connection.db import get_connection
from src.load.B2S_load import run_b2s


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


def _create_bronze_tables(conn):
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bronze_measure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id   TEXT,
            parameter    TEXT NOT NULL,
            unit         TEXT NOT NULL,
            measure_id   TEXT NOT NULL,
            datetime     TEXT NOT NULL,
            value        REAL,
            quality      TEXT,
            completeness TEXT,
            ingested_at  TEXT NOT NULL
        )
    """)
    conn.commit()


def test_run_b2s_uses_latest_ingested_at(tmp_path: Path):
    conn = get_connection(str(tmp_path / "b2s.db"))

    _create_raw_landing(conn)
    _create_bronze_tables(conn)

    old_ts = "2026-02-24T00:00:00+00:00"
    new_ts = "2026-02-25T00:00:00+00:00"

    # raw_landing determines latest ingested_at
    conn.execute("INSERT INTO raw_landing(dataset,payload,ingested_at) VALUES ('station_search','{}',?)", (old_ts,))
    conn.execute("INSERT INTO raw_landing(dataset,payload,ingested_at) VALUES ('station_search','{}',?)", (new_ts,))
    conn.commit()

    # bronze has both batches; silver should take new_ts
    conn.execute("""
        INSERT OR REPLACE INTO bronze_station(station_id,label,ingested_at)
        VALUES ('E64999A','OLD',?)
    """, (old_ts,))
    conn.execute("""
        INSERT OR REPLACE INTO bronze_station(station_id,label,ingested_at)
        VALUES ('E64999A','NEW',?)
    """, (new_ts,))

    conn.execute("""
        INSERT INTO bronze_measure(station_id,parameter,unit,measure_id,datetime,value,ingested_at)
        VALUES ('E64999A','dissolved oxygen','mgL','E64999A-do-i-subdaily-mgL','2026-02-25T00:00:00Z',1.0,?)
    """, (new_ts,))
    conn.commit()

    summary = run_b2s(conn)
    assert summary["status"] == "ok"
    assert summary["ingested_at"] == new_ts

    s = conn.execute("SELECT label, ingested_at FROM silver_station WHERE station_id='E64999A'").fetchone()
    assert s["label"] == "NEW"
    assert s["ingested_at"] == new_ts

    m = conn.execute("SELECT COUNT(*) FROM silver_measure WHERE ingested_at=?", (new_ts,)).fetchone()[0]
    assert m == 1

    conn.close()