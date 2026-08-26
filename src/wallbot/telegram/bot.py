import logging
import time
import telebot
from telebot import apihelper

from src.wallbot.config.settings import TOKEN

# Margen amplio para la conexión HTTP: 10s para conectar, 35s para leer datos
apihelper.CUSTOM_REQUEST_TIMEOUT = (10, 35)


def create_bot() -> telebot.TeleBot:
    logging.info("Creando instancia de bot...")
    return telebot.TeleBot(TOKEN)


def recovery(bot: telebot.TeleBot, initial_delay: int = 2):
    """
    Gestiona el ciclo de vida del polling de Telegram con reconexión limpia.
    """
    logging.info("Iniciando polling con Telegram...")
    while True:
        try:
            # timeout=10 hace que las conexiones se renueven cada 10s de forma ágil
            bot.polling(non_stop=True, timeout=10, long_polling_timeout=10)
        except Exception as err:
            logging.warning("Interrupción en conexión de Telegram: %s. Reintentando en %s s...", err, initial_delay)
            time.sleep(initial_delay)
