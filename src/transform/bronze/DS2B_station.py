import sqlite3
from typing import Any, Dict, List


def create_bronze_station_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bronze_station (
            station_id   TEXT PRIMARY KEY,
            label        TEXT,
            river_name   TEXT,
            lat          REAL,
            long         REAL,
            easting      INTEGER,
            northing     INTEGER,
            status       TEXT,
            ingested_at  TEXT NOT NULL
        )
    """)
    conn.commit()


def station_rows_from_payload(payload: Dict[str, Any], ingested_at: str) -> List[Dict[str, Any]]:
    """
    station_search payload contains items[]; we store them as bronze_station rows.
    """
    items = payload.get("items") or []
    out: List[Dict[str, Any]] = []

    for s in items:
        station_id = s.get("notation")
        if not station_id:
            continue

        status_label = None
        statuses = s.get("status") or []
        if statuses and isinstance(statuses, list):
            status_label = statuses[0].get("label")

        out.append({
            "station_id": station_id,
            "label": s.get("label"),
            "river_name": s.get("riverName"),
            "lat": s.get("lat"),
            "long": s.get("long"),
            "easting": s.get("easting"),
            "northing": s.get("northing"),
            "status": status_label,
            "ingested_at": ingested_at,
        })

    return out


def upsert_bronze_station(conn: sqlite3.Connection, rows: List[Dict[str, Any]]) -> int:
    """
    Upsert because a station can be re-ingested; station_id is stable key.
    """
    if not rows:
        return 0

    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO bronze_station (
            station_id, label, river_name, lat, long, easting, northing, status, ingested_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(station_id) DO UPDATE SET
            label       = excluded.label,
            river_name  = excluded.river_name,
            lat         = excluded.lat,
            long        = excluded.long,
            easting     = excluded.easting,
            northing    = excluded.northing,
            status      = excluded.status,
            ingested_at = excluded.ingested_at
    """, [
        (
            r["station_id"], r.get("label"), r.get("river_name"),
            r.get("lat"), r.get("long"),
            r.get("easting"), r.get("northing"),
            r.get("status"), r["ingested_at"]
        )
        for r in rows
    ])
    conn.commit()
    return cur.rowcount