from utils.logging.logger import logger
from utils.connection.db import get_connection, init_raw_table
from utils.connection.http_client import HttpClient

from config import DB_PATH, BASE_URL, STATION_REF, LIMIT, PARAMETERS, APPEND_MODE

# DS
from validate.ds_validate import validate_bronze_load
from src.load.ds_load import extract_and_load_ds

# DS2B (Bronze structured)
from src.load.DS2B_load import run_ds2b
from validate.bronze_validate import validate_bronze_structured

# B2S (Silver)
from src.load.B2S_load import run_b2s
from validate.silver_validate import validate_silver

# S2G (Gold)
from src.load.S2G_load import run_s2g
from validate.gold_validate import validate_gold


def main():
    log = logger("pipeline", "pipeline", "pipeline.log", "pipeline_error.log")
    log.info("Pipeline started")

    conn = None
    try:
        # DB connection + ensure raw landing table exists (and migrates schema if needed)
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

        # ---------- DS2B LAYER (Bronze structured) ----------
        ds2b_summary = run_ds2b(conn)
        log.info(f"DS2B transform complete: {ds2b_summary}")

        validate_bronze_structured(conn)
        log.info("Bronze structured validation passed.")

        # ---------- B2S LAYER (Silver) ----------
        b2s_summary = run_b2s(conn)
        log.info(f"B2S (Silver) complete: {b2s_summary}")

        validate_silver(conn)
        log.info("Silver validation passed.")

        # ---------- S2G LAYER (Gold) ----------
        s2g_summary = run_s2g(conn)
        log.info(f"S2G (Gold) complete: {s2g_summary}")

        validate_gold(conn)
        log.info("Gold validation passed.")

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