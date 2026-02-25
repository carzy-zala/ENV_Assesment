import sqlite3


def validate_bronze_load(conn: sqlite3.Connection, requested_params: list[str]) -> None:
    """
    Validates bronze landing in raw_landing:

    - Must contain at least 1 station_search row
    - Must contain at least 1 readings row per requested parameter
      (because some params can have multiple units/measures, readings rows may be > len(params))

    Raises RuntimeError if validation fails.
    """
    station_rows = conn.execute(
        "SELECT COUNT(*) FROM raw_landing WHERE dataset = 'station_search'"
    ).fetchone()[0]

    readings_rows = conn.execute(
        "SELECT COUNT(*) FROM raw_landing WHERE dataset LIKE 'readings_latest%'"
    ).fetchone()[0]

    if station_rows < 1:
        raise RuntimeError("Bronze validation failed: station_search row not found in raw_landing.")

    min_expected_readings = len(requested_params)
    if readings_rows < min_expected_readings:
        raise RuntimeError(
            f"Bronze validation failed: expected at least {min_expected_readings} readings rows "
            f"(>= 1 per requested param) but found {readings_rows}."
        )

    min_expected_total = 1 + min_expected_readings
    total_rows = conn.execute("SELECT COUNT(*) FROM raw_landing").fetchone()[0]
    if total_rows < min_expected_total:
        raise RuntimeError(
            f"Bronze validation failed: expected at least {min_expected_total} total raw rows "
            f"but found {total_rows}."
        )