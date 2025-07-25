import locale
import logging
import sys
from logging.handlers import RotatingFileHandler

from src.wallbot.config.settings import PROFILE


def setup_logger():
    log_path = 'wallbot.log'
    level = logging.DEBUG

    if PROFILE is None:
        log_path = '/logs/' + log_path
        level = logging.INFO
        # Configuración solo con archivo cuando PROFILE no está definido
        logging.basicConfig(
            handlers=[RotatingFileHandler(log_path, maxBytes=1000000, backupCount=10)],
            level=level,
            format='%(asctime)s %(message)s',
            datefmt='%m/%d/%Y %H:%M:%S'
        )
    else:
        # Configuración con archivo y salida estándar cuando PROFILE está definido
        logging.basicConfig(
            handlers=[
                RotatingFileHandler(log_path, maxBytes=1000000, backupCount=10),
                logging.StreamHandler(sys.stdout)
            ],
            level=level,
            format='%(asctime)s %(message)s',
            datefmt='%m/%d/%Y %H:%M:%S'
        )

    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
