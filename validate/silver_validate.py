import sqlite3
from datetime import datetime


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def validate_silver(conn: sqlite3.Connection) -> None:
    """
    Validate Silver layer tables and integrity.
    Raises RuntimeError on failure.
    """
    for t in ("silver_station", "silver_measure"):
        if not _table_exists(conn, t):
            raise RuntimeError(f"Silver validation failed: missing table '{t}'")

    station_count = conn.execute("SELECT COUNT(*) FROM silver_station").fetchone()[0]
    if station_count < 1:
        raise RuntimeError("Silver validation failed: silver_station is empty")

    measure_count = conn.execute("SELECT COUNT(*) FROM silver_measure").fetchone()[0]
    if measure_count < 1:
        raise RuntimeError("Silver validation failed: silver_measure is empty")

    # station key fields
    bad_station = conn.execute("""
        SELECT COUNT(*)
        FROM silver_station
        WHERE station_id IS NULL OR station_id = ''
           OR ingested_at IS NULL OR ingested_at = ''
    """).fetchone()[0]
    if bad_station > 0:
        raise RuntimeError(f"Silver validation failed: silver_station has {bad_station} invalid rows (null/blank keys)")

    # measurement required fields
    bad_measure = conn.execute("""
        SELECT COUNT(*)
        FROM silver_measure
        WHERE station_id IS NULL OR station_id = ''
           OR parameter IS NULL OR parameter = ''
           OR unit IS NULL OR unit = ''
           OR measure_id IS NULL OR measure_id = ''
           OR datetime IS NULL OR datetime = ''
           OR ingested_at IS NULL OR ingested_at = ''
    """).fetchone()[0]
    if bad_measure > 0:
        raise RuntimeError(f"Silver validation failed: silver_measure has {bad_measure} invalid rows (null/blank required fields)")

    # datetime parse sanity (sample)
    sample = conn.execute("""
        SELECT datetime
        FROM silver_measure
        ORDER BY id DESC
        LIMIT 20
    """).fetchall()

    for (dt,) in sample:
        try:
            datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            raise RuntimeError(f"Silver validation failed: datetime not ISO format: {dt}")

    # duplicates by business key (should be 0)
    dup = conn.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT measure_id, datetime, ingested_at, COUNT(*) AS c
            FROM silver_measure
            GROUP BY measure_id, datetime, ingested_at
            HAVING c > 1
        )
    """).fetchone()[0]
    if dup > 0:
        raise RuntimeError(f"Silver validation failed: found {dup} duplicate (measure_id, datetime, ingested_at) groups")

    # orphan check: every measurement station exists in station table
    orphan = conn.execute("""
        SELECT COUNT(*)
        FROM silver_measure sm
        LEFT JOIN silver_station ss
          ON ss.station_id = sm.station_id
        WHERE ss.station_id IS NULL
    """).fetchone()[0]
    if orphan > 0:
        raise RuntimeError(f"Silver validation failed: {orphan} measurements have no matching station in silver_station")