import sqlite3
from typing import Any, Dict, List, Tuple


def create_bronze_measure_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bronze_measure (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_bronze_measure_station_dt
        ON bronze_measure(station_id, datetime)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_bronze_measure_measure_id
        ON bronze_measure(measure_id)
    """)
    conn.commit()


def _parse_dataset(dataset: str) -> Tuple[str, str, str]:
    """
    dataset example:
      readings_latest__dissolved_oxygen__E64999A-do-i-subdaily-mgL
    returns:
      (parameter, measure_id, unit)
    """
    parts = dataset.split("__")
    if len(parts) < 3:
        raise ValueError(f"Unexpected dataset format: {dataset}")

    parameter = parts[1].replace("_", " ")
    measure_id = parts[2]

    # unit usually last token after last '-'
    unit = measure_id.split("-")[-1]  # mgL, pct, uS, etc.
    return parameter, measure_id, unit


def measure_rows_from_payload(
    dataset: str,
    payload: Dict[str, Any],
    ingested_at: str,
) -> List[Dict[str, Any]]:
    parameter, measure_id, unit = _parse_dataset(dataset)
    station_id = measure_id.split("-")[0]  # E64999A

    items = payload.get("items") or []
    out: List[Dict[str, Any]] = []

    for r in items:
        dt = r.get("dateTime")
        if not dt:
            continue

        out.append({
            "station_id": station_id,
            "parameter": parameter,
            "unit": unit,
            "measure_id": measure_id,
            "datetime": dt,
            "value": r.get("value"),
            "quality": r.get("quality"),
            "completeness": r.get("completeness"),
            "ingested_at": ingested_at,
        })

    return out


def insert_bronze_measures(conn: sqlite3.Connection, rows: List[Dict[str, Any]]) -> int:
    """
    Append-only: measurements are facts.
    If you want de-dup per run later, we can add a unique constraint.
    """
    if not rows:
        return 0

    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO bronze_measure (
            station_id, parameter, unit, measure_id,
            datetime, value, quality, completeness, ingested_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (
            r.get("station_id"), r["parameter"], r["unit"], r["measure_id"],
            r["datetime"], r.get("value"), r.get("quality"), r.get("completeness"),
            r["ingested_at"]
        )
        for r in rows
    ])
    conn.commit()
    return cur.rowcount