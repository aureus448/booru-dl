"""
Backend for booru access via requests
"""
import logging


def set_logger(log: logging.Logger, name: str):
    """Set up of logging program based on a provided logging.Logger

    Args:
        log (logging.Logger): Logger object to add handlers to
        name (str): Output file name

    Returns:

    """
    log.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    fh = logging.FileHandler(name, mode="w")
    sh.setLevel(logging.INFO)
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%d/%m/%Y | %H:%M:%S"
    )
    sh.setFormatter(formatter)
    fh.setFormatter(formatter)

    log.addHandler(fh)
    log.addHandler(sh)
    return log
