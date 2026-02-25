import sqlite3


def create_silver_measure(conn: sqlite3.Connection) -> None:
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
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_silver_measure_station_dt
        ON silver_measure(station_id, datetime)
    """)
    conn.commit()


def insert_silver_measure_from_bronze(conn: sqlite3.Connection, ingested_at: str) -> int:
    """
    Silver measurement = bronze_measure for given ingested_at,
    deduped and only for stations present in silver_station.
    """
    cur = conn.cursor()

    # insert or ignore avoids duplicates across re-runs for same ingested_at
    cur.execute("""
        INSERT OR IGNORE INTO silver_measure (
            station_id, parameter, unit, measure_id, datetime, value, quality, completeness, ingested_at
        )
        SELECT
            bm.station_id,
            lower(bm.parameter) as parameter,
            bm.unit,
            bm.measure_id,
            -- normalize Z -> +00:00 so ISO parsing works consistently later
            replace(bm.datetime, 'Z', '+00:00') as datetime,
            bm.value,
            bm.quality,
            bm.completeness,
            bm.ingested_at
        FROM bronze_measure bm
        INNER JOIN silver_station ss
            ON ss.station_id = bm.station_id
        WHERE bm.ingested_at = ?
    """, (ingested_at,))

    conn.commit()
    return cur.rowcount