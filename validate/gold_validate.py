import sqlite3


def validate_gold(conn: sqlite3.Connection) -> None:
    # tables exist
    for t in ("fact_station", "dim_measurement"):
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (t,),
        ).fetchone()
        if not row:
            raise RuntimeError(f"Gold validation failed: missing table {t}")

    # row counts
    s = conn.execute("SELECT COUNT(*) FROM fact_station").fetchone()[0]
    f = conn.execute("SELECT COUNT(*) FROM dim_measurement").fetchone()[0]

    if s < 1:
        raise RuntimeError("Gold validation failed: fact_station is empty")
    if f < 1:
        raise RuntimeError("Gold validation failed: dim_measurement is empty")

    # FK integrity sanity (no missing station_key)
    bad = conn.execute("""
        SELECT COUNT(*) FROM dim_measurement
        WHERE station_key IS NULL
    """).fetchone()[0]
    if bad > 0:
        raise RuntimeError(f"Gold validation failed: {bad} fact rows missing station_key")