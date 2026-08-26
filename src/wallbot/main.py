import logging
import threading

from src.wallbot.config.settings import APP_VERSION
from src.wallbot.database.db_helper import DBHelper
from src.wallbot.telegram.bot import create_bot, recovery
from src.wallbot.telegram.handlers import TelegramHandlers
from src.wallbot.telegram.notifications import notify_startup
from src.wallbot.utils.logger import setup_logger
from src.wallbot.wallapop.monitor import WallapopMonitor


def main():
    setup_logger()
    logging.info("Iniciando Wallbot v%s...", APP_VERSION)

    # Inicializar Base de Datos con la versión actual
    db = DBHelper()
    db.setup(APP_VERSION)
    logging.info("Base de datos inicializada correctamente.")

    # Crear instancia del Bot de Telegram
    bot = create_bot()

    # Registrar los manejadores de comandos
    TelegramHandlers(bot, db)
    logging.info("Manejadores de Telegram registrados.")

    # Iniciar el monitor de Wallapop en segundo plano (daemon thread)
    monitor = WallapopMonitor(db)
    threading.Thread(target=monitor.start, daemon=True).start()
    logging.info("Servicio de monitorización de Wallapop activo y rastreando anuncios.")

    # Enviar notificación de arranque con la versión al primer usuario/admin
    notify_startup(bot)

    # Iniciar el bucle de escucha de Telegram (con 1s de retardo inicial)
    logging.info("Bot de Telegram autenticado y escuchando mensajes.")
    recovery(bot, 1)


if __name__ == '__main__':
    main()
