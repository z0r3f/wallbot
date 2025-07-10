import logging
import threading

from src.wallbot.telegram.handlers import TelegramHandlers
from .database.db_helper import DBHelper
from .telegram.bot import create_bot, recovery
from .utils.logger import setup_logger
from .utils.version import read_version
from .wallapop.monitor import WallapopMonitor


def main():
    setup_logger()
    logging.info("JanJanJan starting...")

    db = DBHelper()
    db.setup(read_version())

    bot = create_bot()

    TelegramHandlers(bot, db)

    monitor = WallapopMonitor(db)
    threading.Thread(target=monitor.start, daemon=True).start()

    recovery(bot, 1)


if __name__ == '__main__':
    main()
