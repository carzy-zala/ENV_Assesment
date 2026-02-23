from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.connection.db import get_connection

def test_get_connection_creates_db_file(tmp_path: Path):
    db_path = tmp_path / "my_test.db"

    conn = get_connection(str(db_path))
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")
    conn.commit()
    conn.close()

    assert db_path.exists()


def test_get_connection_enables_foreign_keys(tmp_path: Path):
    db_path = tmp_path / "fk_test.db"
    conn = get_connection(str(db_path))

    fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
    conn.close()

    assert fk == 1
    