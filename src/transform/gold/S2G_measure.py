import sqlite3


def create_dim_measurement(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dim_measurement (
            measurement_key INTEGER PRIMARY KEY AUTOINCREMENT,
            station_key     INTEGER NOT NULL,
            station_id      TEXT NOT NULL,
            parameter       TEXT NOT NULL,
            unit            TEXT NOT NULL,
            measure_id      TEXT NOT NULL,
            datetime        TEXT NOT NULL,
            value           REAL,
            quality         TEXT,
            completeness    TEXT,
            ingested_at     TEXT NOT NULL,

            FOREIGN KEY(station_key) REFERENCES fact_station(station_key),
            UNIQUE(measure_id, datetime, ingested_at)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_fact_station_dt
        ON dim_measurement(station_id, datetime)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_dim_param_unit
        ON dim_measurement(parameter, unit)
    """)
    conn.commit()


def insert_dim_measurement_from_silver(conn: sqlite3.Connection, ingested_at: str) -> int:
    """
    Insert measurements for this batch, joined to fact_station to get station_key.
    Deduped via UNIQUE + INSERT OR IGNORE.
    """
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO dim_measurement (
            station_key, station_id, parameter, unit, measure_id, datetime,
            value, quality, completeness, ingested_at
        )
        SELECT
            ds.station_key,
            sm.station_id,
            sm.parameter,
            sm.unit,
            sm.measure_id,
            sm.datetime,
            sm.value,
            sm.quality,
            sm.completeness,
            sm.ingested_at
        FROM silver_measure sm
        INNER JOIN fact_station ds
            ON ds.station_id = sm.station_id
        WHERE sm.ingested_at = ?
    """, (ingested_at,))
    conn.commit()
    return cur.rowcount