import sqlite3


def validate_gold(conn: sqlite3.Connection) -> None:
    # tables exist
    for t in ("dim_station", "fact_measurement"):
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (t,),
        ).fetchone()
        if not row:
            raise RuntimeError(f"Gold validation failed: missing table {t}")

    # row counts
    s = conn.execute("SELECT COUNT(*) FROM dim_station").fetchone()[0]
    f = conn.execute("SELECT COUNT(*) FROM fact_measurement").fetchone()[0]

    if s < 1:
        raise RuntimeError("Gold validation failed: dim_station is empty")
    if f < 1:
        raise RuntimeError("Gold validation failed: fact_measurement is empty")

    # FK integrity sanity (no missing station_key)
    bad = conn.execute("""
        SELECT COUNT(*) FROM fact_measurement
        WHERE station_key IS NULL
    """).fetchone()[0]
    if bad > 0:
        raise RuntimeError(f"Gold validation failed: {bad} fact rows missing station_key")