import sqlite3
from pathlib import Path
from utils.errorHandling.errors import LoadError
from datetime import datetime, timezone

def get_connection(db_path: str) -> sqlite3.Connection:
    """
    Create/connect to a SQLite database (file-based).
    Ensures parent folder exists.
    """
    try:
        path = Path(db_path)
        if path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        raise LoadError(f"Failed to connect to SQLite at {db_path}: {e}") from e


# --- NEW: raw landing schema ---

def init_raw_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_landing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset TEXT NOT NULL,
            payload TEXT NOT NULL,
            ingested_at TEXT NOT NULL
        )
    """)
    conn.commit()


def insert_raw_payload(conn: sqlite3.Connection, dataset: str, payload_json: str, ingested_at: str | None = None) -> None:
    if ingested_at is None:
        ingested_at = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT INTO raw_landing(dataset, payload, ingested_at) VALUES (?, ?, ?)",
        (dataset, payload_json, ingested_at),
    )
    conn.commit()

def delete_datasets(conn: sqlite3.Connection, datasets: list[str]) -> None:
    """
    Delete specific datasets from raw_landing (overwrite mode).
    """
    try:
        conn.executemany(
            "DELETE FROM raw_landing WHERE dataset = ?",
            [(d,) for d in datasets]
        )
        conn.commit()
    except sqlite3.Error as e:
        raise LoadError(f"Failed to delete datasets from raw_landing: {e}") from e
