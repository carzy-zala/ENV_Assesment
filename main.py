from utils.logging.logger import logger
from utils.connection.db import get_connection
from config import DB_PATH

def main():
    log = logger("pipeline", "pipeline", "pipeline.log", "pipeline_error.log")
    log.info("Pipeline started")

    conn = get_connection(DB_PATH)

    log.info("SQLite connection established and raw tables created.")
    conn.close()

    log.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()