import sqlite3
from datetime import datetime


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def validate_bronze_structured(conn: sqlite3.Connection) -> None:
    """
    Validates DS2B output tables: bronze_station and bronze_measure.
    Raises RuntimeError on failure.
    """

    # --- Table existence ---
    if not _table_exists(conn, "bronze_station"):
        raise RuntimeError("Bronze validation failed: bronze_station table not found.")
    if not _table_exists(conn, "bronze_measure"):
        raise RuntimeError("Bronze validation failed: bronze_measure table not found.")

    # --- Row counts ---
    station_count = conn.execute("SELECT COUNT(*) FROM bronze_station").fetchone()[0]
    if station_count < 1:
        raise RuntimeError("Bronze validation failed: bronze_station has 0 rows.")

    measure_count = conn.execute("SELECT COUNT(*) FROM bronze_measure").fetchone()[0]
    if measure_count < 1:
        raise RuntimeError("Bronze validation failed: bronze_measure has 0 rows.")

    # --- Null checks (station) ---
    bad_station = conn.execute("""
        SELECT COUNT(*)
        FROM bronze_station
        WHERE station_id IS NULL OR station_id = ''
           OR label IS NULL OR label = ''
           OR ingested_at IS NULL OR ingested_at = ''
    """).fetchone()[0]
    if bad_station > 0:
        raise RuntimeError(f"Bronze validation failed: bronze_station has {bad_station} invalid rows (null/blank key fields).")

    # --- Null checks (measure) ---
    bad_measure = conn.execute("""
        SELECT COUNT(*)
        FROM bronze_measure
        WHERE station_id IS NULL OR station_id = ''
           OR parameter IS NULL OR parameter = ''
           OR unit IS NULL OR unit = ''
           OR measure_id IS NULL OR measure_id = ''
           OR datetime IS NULL OR datetime = ''
           OR ingested_at IS NULL OR ingested_at = ''
    """).fetchone()[0]
    if bad_measure > 0:
        raise RuntimeError(f"Bronze validation failed: bronze_measure has {bad_measure} invalid rows (null/blank required fields).")

    # --- Datetime parse sanity (basic) ---
    # Keep it light: just try parsing the first few rows.
    sample = conn.execute("""
        SELECT datetime
        FROM bronze_measure
        ORDER BY id DESC
        LIMIT 20
    """).fetchall()

    for (dt,) in sample:
        try:
            # Handles "2026-02-25T00:00:00Z" by stripping trailing Z
            datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            raise RuntimeError(f"Bronze validation failed: datetime not ISO format: {dt}")

    # --- Duplicate check within same ingestion run (optional but strong) ---
    dup = conn.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT measure_id, datetime, ingested_at, COUNT(*) AS c
            FROM bronze_measure
            GROUP BY measure_id, datetime, ingested_at
            HAVING c > 1
        )
    """).fetchone()[0]
    if dup > 0:
        raise RuntimeError(f"Bronze validation failed: found {dup} duplicate (measure_id, datetime, ingested_at) groups.")