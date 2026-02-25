from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.connection.db import get_connection
from src.transform.silver.B2S_station import create_silver_station
from src.transform.silver.B2S_measure import (
    create_silver_measure,
    insert_silver_measure_from_bronze,
)


def _create_bronze_measure(conn):
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


def test_create_silver_measure_creates_table_and_unique(tmp_path: Path):
    conn = get_connection(str(tmp_path / "m.db"))
    create_silver_measure(conn)

    # table exists
    row = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='silver_measure'
    """).fetchone()
    assert row is not None

    # UNIQUE index created implicitly; we just ensure inserts dedupe in next test
    conn.close()


def test_insert_silver_measure_from_bronze_inserts_and_dedupes(tmp_path: Path):
    conn = get_connection(str(tmp_path / "m2.db"))

    # bronze tables
    _create_bronze_measure(conn)

    # silver tables
    create_silver_station(conn)
    create_silver_measure(conn)

    ts = "2026-02-25T00:00:00+00:00"

    # station must exist in silver_station for the INNER JOIN
    conn.execute("""
        INSERT INTO silver_station(station_id, label, ingested_at)
        VALUES ('E64999A', 'HIPPER_PARK ROAD BRIDGE_E_202312', ?)
    """, (ts,))
    conn.commit()

    # Insert duplicate readings in bronze for same (measure_id, datetime, ingested_at)
    conn.execute("""
        INSERT INTO bronze_measure(station_id, parameter, unit, measure_id, datetime, value, ingested_at)
        VALUES ('E64999A', 'Dissolved Oxygen', 'mgL', 'E64999A-do-i-subdaily-mgL', '2026-02-25T00:00:00Z', 1.23, ?)
    """, (ts,))
    conn.execute("""
        INSERT INTO bronze_measure(station_id, parameter, unit, measure_id, datetime, value, ingested_at)
        VALUES ('E64999A', 'Dissolved Oxygen', 'mgL', 'E64999A-do-i-subdaily-mgL', '2026-02-25T00:00:00Z', 1.23, ?)
    """, (ts,))
    conn.commit()

    inserted = insert_silver_measure_from_bronze(conn, ts)
    # first insert may report 1 or 2 depending on sqlite cursor semantics,
    # so assert final table count, not cursor count.
    assert inserted >= 1

    c = conn.execute("""
        SELECT COUNT(*) FROM silver_measure
        WHERE measure_id='E64999A-do-i-subdaily-mgL' AND ingested_at=?
    """, (ts,)).fetchone()[0]

    # deduped to 1 due to UNIQUE + INSERT OR IGNORE
    assert c == 1

    # datetime normalized (Z -> +00:00)
    dt = conn.execute("""
        SELECT datetime FROM silver_measure
        WHERE measure_id='E64999A-do-i-subdaily-mgL' AND ingested_at=?
    """, (ts,)).fetchone()[0]
    assert dt.endswith("+00:00")

    conn.close()


def test_insert_silver_measure_from_bronze_skips_orphan_station(tmp_path: Path):
    conn = get_connection(str(tmp_path / "m3.db"))

    _create_bronze_measure(conn)
    create_silver_station(conn)
    create_silver_measure(conn)

    ts = "2026-02-25T00:00:00+00:00"

    # bronze has measurement but silver_station DOES NOT have station -> should not load
    conn.execute("""
        INSERT INTO bronze_measure(station_id, parameter, unit, measure_id, datetime, value, ingested_at)
        VALUES ('E99999X', 'conductivity', 'uS', 'E99999X-cond-i-subdaily-uS', '2026-02-25T00:00:00Z', 200.0, ?)
    """, (ts,))
    conn.commit()

    inserted = insert_silver_measure_from_bronze(conn, ts)
    assert inserted == 0

    c = conn.execute("SELECT COUNT(*) FROM silver_measure").fetchone()[0]
    assert c == 0

    conn.close()