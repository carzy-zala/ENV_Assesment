import sqlite3


def create_silver_station(conn: sqlite3.Connection) -> None:
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
    conn.commit()


def upsert_silver_station_from_bronze(conn: sqlite3.Connection, ingested_at: str) -> int:
    """
    Silver station = latest snapshot per station_id for the given ingested_at batch.
    """
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO silver_station (
            station_id, label, river_name, lat, long, easting, northing, status, ingested_at
        )
        SELECT
            station_id, label, river_name, lat, long, easting, northing, status, ingested_at
        FROM bronze_station
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