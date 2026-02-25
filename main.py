from utils.logging.logger import logger
from utils.connection.db import get_connection, init_raw_table
from utils.connection.http_client import HttpClient
from config import DB_PATH, BASE_URL, STATION_REF, LIMIT, PARAMETERS, APPEND_MODE
from validate.ds_validate import validate_bronze_load
from src.load.ds_load import extract_and_load_ds


def main():
    log = logger("pipeline", "pipeline", "pipeline.log", "pipeline_error.log")
    log.info("Pipeline started")

    conn = None
    try:
        # DB connection + ensure raw landing table exists
        conn = get_connection(DB_PATH)
        init_raw_table(conn)
        log.info("SQLite connection established and raw_landing table ready.")

        # HTTP client
        client = HttpClient(BASE_URL)

        # Extract + load bronze into SQLite
        summary = extract_and_load_ds(
            conn=conn,
            client=client,
            station_ref=STATION_REF,
            requested_params=PARAMETERS,
            limit=LIMIT,
            append_mode=APPEND_MODE,
        )

        log.info(f"Bronze load complete: {summary}")
        validate_bronze_load(conn, PARAMETERS)
        log.info("Bronze validation passed.")

    except Exception as e:
        # log exception with stack trace
        log.exception(f"Pipeline failed: {e}")
        raise
    finally:
        if conn:
            conn.close()
            log.info("SQLite connection closed.")

    log.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()