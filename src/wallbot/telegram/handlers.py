import logging
import textwrap
from re import sub

import telebot

from src.wallbot.database.db_helper import DBHelper
from src.wallbot.database.models import ChatSearch


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

    def send_welcome(self, message):
        welcome_text = textwrap.dedent("""\
            *Utilización*
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

    def add_search(self, message):
        cs = ChatSearch()
        cs.chat_id = message.chat.id
        parameters = str(message.text).split(' ', 1)
        if len(parameters) < 2:
            # Solo puso el comando
            return
        token = ' '.join(parameters[1:]).split(',')
        if len(token) < 1:
            # Puso un espacio después del comando, nada más
            return
        cs.kws = token[0].strip()
        if len(token) > 1:
            rango = token[1].split('-')
            cs.min_price = rango[0].strip()
            if len(rango) > 1:
                cs.max_price = rango[1].strip()
        if len(token) > 2:
            cs.cat_ids = sub('[\s+]', '', ','.join(token[2:]))
            if len(cs.cat_ids) == 0:
                cs.cat_ids = None
        cs.username = message.from_user.username
        cs.name = message.from_user.first_name
        cs.active = 1
        logging.info('%s', cs)
        self.db.add_search(cs)

    def delete_search(self, message):
        parameters = str(message.text).split(' ', 1)
        if len(parameters) < 2:
            return
        self.db.del_chat_search(message.chat.id, ' '.join(parameters[1:]))

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
            self.bot.send_message(message.chat.id, (text,))
