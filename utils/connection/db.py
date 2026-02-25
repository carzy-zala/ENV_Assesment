import sqlite3
from pathlib import Path
from utils.errorHandling.errors import LoadError


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
    """
    Create the raw landing table if it does not exist.
    Stores raw JSON payloads exactly as received.
    """
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_landing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset TEXT NOT NULL,
                payload TEXT NOT NULL
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        raise LoadError(f"Failed to create raw_landing table: {e}") from e


def insert_raw_payload(conn: sqlite3.Connection, dataset: str, payload_json: str) -> None:
    """
    Insert raw JSON payload into raw_landing table.
    """
    try:
        conn.execute(
            "INSERT INTO raw_landing(dataset, payload) VALUES (?, ?)",
            (dataset, payload_json),
        )
        conn.commit()
    except sqlite3.Error as e:
        raise LoadError(f"Failed to insert raw payload: {e}") from e