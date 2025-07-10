import logging
import time

import telebot

from src.wallbot.config.settings import TOKEN


def create_bot():
    logging.info("Creating bot...")
    return telebot.TeleBot(TOKEN)


def recovery(bot, times):
    try:
        time.sleep(times)
        logging.info("Conexión a Telegram.")
        bot.polling(none_stop=True, timeout=3000)
    except Exception as e:
        logging.error("Ha ocurrido un error con la llamada a Telegram. Se reintenta la conexión", e)
        print("Ha ocurrido un error con la llamada a Telegram. Se reintenta la conexión")
        if times > 16:
            times = 16
        recovery(bot, times * 2)
