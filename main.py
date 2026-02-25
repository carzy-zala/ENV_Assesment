from utils.logging.logger import logger
from utils.connection.db import get_connection, init_raw_table
from utils.connection.http_client import HttpClient

from config import DB_PATH, BASE_URL, STATION_REF, LIMIT, PARAMETERS, APPEND_MODE

from validate.ds_validate import validate_bronze_load
from src.load.ds_load import extract_and_load_ds

from src.load.DS2B_load import run_ds2b
from src.load.B2S_load import run_b2s



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

        # ---------- DS LAYER ----------
        ds_summary = extract_and_load_ds(
            conn=conn,
            client=client,
            station_ref=STATION_REF,
            requested_params=PARAMETERS,
            limit=LIMIT,
            append_mode=APPEND_MODE,
        )
        log.info(f"DS load complete: {ds_summary}")

        # DS validation
        validate_bronze_load(conn, PARAMETERS)
        log.info("DS validation passed.")

        # ---------- DS2B LAYER ----------
        ds2b_summary = run_ds2b(conn)
        log.info(f"DS2B transform complete: {ds2b_summary}")
        

        b2s_summary = run_b2s(conn)
        log.info(f"B2S (Silver) complete: {b2s_summary}")

    except Exception as e:
        log.exception(f"Pipeline failed: {e}")
        raise
    finally:
        if conn:
            conn.close()
            log.info("SQLite connection closed.")

    log.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()