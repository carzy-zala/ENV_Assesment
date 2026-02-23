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