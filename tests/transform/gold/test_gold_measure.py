from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from utils.connection.db import get_connection
from src.transform.gold.S2G_station import create_dim_station
from src.transform.gold.S2G_measure import create_fact_measurement, insert_fact_measurement_from_silver


def _create_silver_measure(conn):
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


def _seed_dim_station(conn, ts: str):
    # create a dim row so fact insert can join to get station_key
    conn.execute("""
        INSERT INTO dim_station(station_id,label,ingested_at)
        VALUES ('E64999A','HIPPER',?)
    """, (ts,))
    conn.commit()


def test_create_fact_measurement_creates_table(tmp_path: Path):
    conn = get_connection(str(tmp_path / "g_meas_1.db"))
    create_dim_station(conn)         # referenced by FK
    create_fact_measurement(conn)

    row = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='fact_measurement'
    """).fetchone()

    conn.close()
    assert row is not None


def test_insert_fact_measurement_from_silver_inserts_and_dedupes(tmp_path: Path):
    conn = get_connection(str(tmp_path / "g_meas_2.db"))
    _create_silver_measure(conn)
    create_dim_station(conn)
    create_fact_measurement(conn)

    ts = "2026-02-25T00:00:00+00:00"
    _seed_dim_station(conn, ts)

    # Insert 1 silver measure row
    conn.execute("""
        INSERT INTO silver_measure(station_id,parameter,unit,measure_id,datetime,value,quality,completeness,ingested_at)
        VALUES ('E64999A','dissolved oxygen','mgL','E64999A-do-i-subdaily-mgL','2026-02-25T00:00:00+00:00',1.0,'Good','Complete',?)
    """, (ts,))
    conn.commit()

    # Run insert twice -> should stay 1 due to UNIQUE + INSERT OR IGNORE
    insert_fact_measurement_from_silver(conn, ts)
    insert_fact_measurement_from_silver(conn, ts)

    c = conn.execute("""
        SELECT COUNT(*) FROM fact_measurement
        WHERE measure_id='E64999A-do-i-subdaily-mgL' AND datetime='2026-02-25T00:00:00+00:00' AND ingested_at=?
    """, (ts,)).fetchone()[0]

    # station_key should be populated
    station_key = conn.execute("""
        SELECT station_key FROM fact_measurement
        WHERE ingested_at=?
        LIMIT 1
    """, (ts,)).fetchone()[0]

    conn.close()

    assert c == 1
    assert station_key is not None