from pathlib import Path
from utils.logging.logger import logger


def main():
    Path("data").mkdir(exist_ok=True)

    log = logger(
        name="pipeline",
        folder="pipeline",
        info_file="pipeline.log",
        error_file="pipeline_error.log",
    )

    log.info("Pipeline started")

    try:
        log.info("Environment ready")

        log.info("Pipeline finished successfully")

    except Exception as e:
        log.exception(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()