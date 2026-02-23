import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,  # Docker captures stdout/stderr
        force=True,
    )
    return logging.getLogger(__name__)



def telegram_logging():
    # TODO greate a telegram channel for iunforming the admin of changes and errors
    raise NotImplementedError
    pass