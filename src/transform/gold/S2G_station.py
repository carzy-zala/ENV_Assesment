import sqlite3


def create_fact_station(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fact_station (
            station_key INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id  TEXT NOT NULL UNIQUE,
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
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_station_station_id ON fact_station(station_id)")
    conn.commit()


def upsert_fact_station_from_silver(conn: sqlite3.Connection, ingested_at: str) -> int:
    """
    Upsert the station dimension using the latest silver snapshot for this batch.
    """
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO fact_station (
            station_id, label, river_name, lat, long, easting, northing, status, ingested_at
        )
        SELECT
            station_id, label, river_name, lat, long, easting, northing, status, ingested_at
        FROM silver_station
        WHERE ingested_at = ?
        ON CONFLICT(station_id) DO UPDATE SET
            label       = excluded.label,
            river_name  = excluded.river_name,
            lat         = excluded.lat,
            long        = excluded.long,
            easting     = excluded.easting,
            northing    = excluded.northing,
            status      = excluded.status,
            ingested_at = excluded.ingested_at
    """, (ingested_at,))
    conn.commit()
    return cur.rowcount