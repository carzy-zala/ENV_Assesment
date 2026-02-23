import logging
from pathlib import Path


def logger(
    name: str,
    folder: str,
    info_file: str,
    error_file: str,
    console: bool = True,
    level: int = logging.INFO
) -> logging.Logger:
    """
    - INFO+ logs -> logs/<folder>/<info_file>
    - ERROR+ logs -> logs/<folder>/<error_file>
    - Optional console output
    """

    log_dir = Path("logs") / folder
    log_dir.mkdir(parents=True, exist_ok=True)

    log = logging.getLogger(name)
    log.setLevel(level)
    log.propagate = False

    # remove existing handlers
    if log.handlers:
        for h in list(log.handlers):
            log.removeHandler(h)
            h.close()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    
    # saperating info and error logs

    # info log cretaion 
    info_handler = logging.FileHandler(log_dir / info_file, encoding="utf-8")
    info_handler.setLevel(level)
    info_handler.setFormatter(formatter)

    # error log creation 
    error_handler = logging.FileHandler(log_dir / error_file, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    log.addHandler(info_handler)
    log.addHandler(error_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        log.addHandler(console_handler)

    return log