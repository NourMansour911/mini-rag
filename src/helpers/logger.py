import logging
from logging.handlers import RotatingFileHandler
import os


LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "logs.log")

def get_logger(name: str, level=logging.DEBUG):

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.hasHandlers():
        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

        # File handler with rotation
        fh = RotatingFileHandler(
            LOG_FILE, maxBytes=5_000_000, backupCount=5
        )
        fh.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger