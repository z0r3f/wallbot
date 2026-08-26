import functools
import logging
import textwrap
from re import sub

import telebot

from src.wallbot.config.settings import APP_VERSION, AUTHORIZED_USERS
from src.wallbot.database.db_helper import DBHelper
from src.wallbot.database.models import ChatSearch


def restricted(func):
    """Decorador para restringir la ejecución de comandos a usuarios autorizados."""
    @functools.wraps(func)
    def wrapper(self, message, *args, **kwargs):
        # Si la lista está vacía, se permite el acceso libre (o puedes bloquearlo por defecto)
        if not AUTHORIZED_USERS:
            return func(self, message, *args, **kwargs)

        user_id = str(message.from_user.id)
        username = (message.from_user.username or "").lower()

        # Comprueba tanto el ID numérico como el alias (username)
        if user_id in AUTHORIZED_USERS or username in AUTHORIZED_USERS:
            return func(self, message, *args, **kwargs)

        logging.warning(
            "Acceso no autorizado intentado por User ID: %s (Username: @%s)",
            user_id,
            username or "sin_alias"
        )
        self.bot.send_message(
            message.chat.id,
            "⛔ *Acceso denegado:* No tienes autorización para interactuar con este bot.",
            parse_mode="Markdown"
        )
        return None

    return wrapper


class TelegramHandlers:
    def __init__(self, bot: telebot.TeleBot, db: DBHelper):
        self.bot = bot
        self.db = db
        self._register_handlers()

    def _register_handlers(self):
        self.bot.message_handler(commands=['start', 'help', 's', 'h'])(self.send_welcome)
        self.bot.message_handler(commands=['add', 'añadir', 'append', 'a'])(self.add_search)
        self.bot.message_handler(commands=['del', 'borrar', 'd'])(self.delete_search)
        self.bot.message_handler(commands=['lis', 'listar', 'l'])(self.get_searches)

    @restricted
    def send_welcome(self, message):
        welcome_text = textwrap.dedent(f"""\
            🤖 *Wallbot* `v{APP_VERSION}`

            *Utilización:*
            /help

            *Añadir búsquedas:*
            \t/add `búsqueda,min-max`
            \t/add zapatos rojos,5-25

            *Borrar búsqueda:*
            \t/del `búsqueda`
            \t/del zapatos rojos

            *Lista de búsquedas:*
            \t/lis
        """)
        self.bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')


    @restricted
    def add_search(self, message):
        cs = ChatSearch()
        cs.chat_id = message.chat.id
        parameters = str(message.text).split(' ', 1)
        if len(parameters) < 2:
            return
        token = ' '.join(parameters[1:]).split(',')
        if len(token) < 1:
            return
        cs.kws = token[0].strip()
        if len(token) > 1:
            rango = token[1].split('-')
            cs.min_price = rango[0].strip()
            if len(rango) > 1:
                cs.max_price = rango[1].strip()
        if len(token) > 2:
            cs.cat_ids = sub(r'[\s+]', '', ','.join(token[2:]))
            if len(cs.cat_ids) == 0:
                cs.cat_ids = None
        cs.username = message.from_user.username
        cs.name = message.from_user.first_name
        cs.active = 1
        logging.info('%s', cs)
        self.db.add_search(cs)

    @restricted
    def delete_search(self, message):
        parameters = str(message.text).split(' ', 1)
        if len(parameters) < 2:
            return
        self.db.del_chat_search(message.chat.id, ' '.join(parameters[1:]))

    @restricted
    def get_searches(self, message):
        text = ''
        for chat_search in self.db.get_chat_searches(message.chat.id):
            if len(text) > 0:
                text += '\n'
            text += chat_search.kws
            text += '|'
            if chat_search.min_price is not None:
                text += chat_search.min_price
            text += '-'
            if chat_search.max_price is not None:
                text += chat_search.max_price
            if chat_search.cat_ids is not None:
                text += '|'
                text += chat_search.cat_ids
        if len(text) > 0:
            self.bot.send_message(message.chat.id, text)
        else:
            self.bot.send_message(message.chat.id, "Lista vacía")
