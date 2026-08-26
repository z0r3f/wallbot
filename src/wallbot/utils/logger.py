import locale
import logging
import sys
from logging.handlers import RotatingFileHandler

from src.wallbot.config.settings import DEBUG, LOG_PATH


def setup_logger():
    # En producción se registran eventos INFO; en desarrollo eventos DEBUG
    level = logging.DEBUG if DEBUG else logging.INFO

    # Handlers: siempre escribe en archivo rotativo y en stdout (consola de Docker)
    handlers = [
        RotatingFileHandler(
            LOG_PATH, maxBytes=1_000_000, backupCount=10, encoding="utf-8"
        ),
        logging.StreamHandler(sys.stdout),
    ]

    logging.basicConfig(
        handlers=handlers,
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        force=True,
    )

    try:
        locale.setlocale(locale.LC_ALL, "es_ES.UTF-8")
    except locale.Error:
        locale.setlocale(locale.LC_ALL, "")
