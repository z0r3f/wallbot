#!/usr/bin/python3.5

import requests
import time
import telebot
import logging
import threading
import os
import locale
from dbhelper import DBHelper, ChatSearch, Item
from re import sub
from decimal import Decimal
from logging.handlers import RotatingFileHandler
from telebot import TeleBot
from telebot import types
from telebot.types import InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from urllib.parse import urlparse

TOKEN = os.getenv("BOT_TOKEN", "Bot Token does not exist")
URL_ITEMS = "https://api.wallapop.com/api/v3/general/search"
URL_CATEGORIES = "https://api.wallapop.com/api/v3/categories"
PROFILE = os.getenv("PROFILE")

if PROFILE is None:
    db = DBHelper()
else:
    db = DBHelper("db.sqlite")


ICON_VIDEO_GAMES = u'\U0001F3AE'  # 🎮
ICON_WARNING____ = u'\U000026A0'  # ⚠️
ICON_HIGH_VOLTAG = u'\U000026A1'  # ⚡️
ICON_COLLISION__ = u'\U0001F4A5'  # 💥
ICON_EXCLAMATION = u'\U00002757'  # ❗
ICON_DIRECT_HIT_ = u'\U0001F3AF'  # 🎯
ICON_ARROW       = u'\U000027A1'  # ➡


def notel(chat_id, price, title, description, creation_date, url_item, obs=None, images=None):
    try:
        archivo = urlparse(images[0]['original'])
        nombreArchivo = os.path.basename(archivo.path)
        rutaArchivo = "/data/media/" + nombreArchivo

        response = requests.get(images[0]['original'])
        open(rutaArchivo, "wb").write(response.content)

        with open(rutaArchivo, 'rb') as fh:
            image = fh.read()

        bot.send_photo(chat_id, image, disable_notification=True)
        os.remove(rutaArchivo)
    except Exception as e:
        logging.error(e)

    if obs is not None:
        text = ICON_EXCLAMATION
    else:
        text = ICON_DIRECT_HIT_

    text += ' <b>' + title + '</b>'
    text += '\n\n'

    text += "<b>Descripción: </b>" + description
    text += '\n\n'

    text += "<b>Fecha de publicación: </b>" + creation_date
    text += '\n\n'

    text += "<b>Precio: </b>" + locale.currency(price, grouping=True)
    text += '\n\n'

    if obs is not None:
        text += ICON_COLLISION__ + ' '

    if obs is not None:
        text += obs
        text += ' ' + ICON_COLLISION__

    text += '\n'
    urlAnuncio = 'https://es.wallapop.com/item/' + url_item

    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text='Ir al anuncio', url=urlAnuncio)]]))


def get_url_list(search):
    url = URL_ITEMS
    url += '?keywords='
    url += "+".join(search.kws.split(" "))
    url += '&time_filter=today'
    if search.cat_ids is not None:
        url += '&category_ids='
        url += search.cat_ids
    if search.min_price is not None:
        url += '&min_sale_price='
        url += search.min_price
    if search.max_price is not None:
        url += '&max_sale_price='
        url += search.max_price
    if search.dist is not None:
        url += '&dist='
        url += search.dist
    if search.orde is not None:
        url += '&order_by='
        url += search.orde
    return url


def get_items(url, chat_id):
    try:
        resp = requests.get(url=url)
        data = resp.json()
        for producto in data['search_objects']:
            logging.info('Encontrado: id=%s, price=%s, title=%s, user=%s',str(producto['id']), locale.currency(producto['price'], grouping=True), producto['title'], producto['user']['id'])
            i = db.search_item(producto['id'], chat_id)
            if i is None:
                creationDate = datetime.fromtimestamp(producto['creation_date'] / 1000).strftime("%d/%m/%Y %H:%M:%S")
                db.add_item(producto['id'], chat_id, producto['title'], producto['price'], producto['web_slug'], producto['user']['id'], creationDate)
                notel(chat_id, producto['price'], producto['title'], producto['description'], creationDate, producto['web_slug'], None, producto['images'])
                logging.info('New: id=%s, price=%s, title=%s', str(producto['id']), locale.currency(producto['price'], grouping=True), producto['title'])
            else:
                # Si está comparar precio...
                money = str(producto['price'])
                value_json = Decimal(sub(r'[^\d.]', '', money))
                value_db = Decimal(sub(r'[^\d.]', '', i.price))
                if value_json < value_db:
                    new_obs = locale.currency(i.price, grouping=True)
                    if i.observaciones is not None:
                        new_obs += ' < '
                        new_obs += i.observaciones
                    db.update_item(producto['id'], money, new_obs)
                    obs = ' < ' + new_obs
                    notel(chat_id, producto['price'], producto['title'], producto['web_slug'], obs)
                    logging.info('Baja: id=%s, price=%s, title=%s', str(producto['id']), locale.currency(producto['price'], grouping=True), producto['title'])
    except Exception as e:
        logging.error(e)


def get_categories(url):
    try:
        resp = requests.get(url=url, headers={"Accept-Language": "es-ES"})
        data = resp.json()
        return data
    
    except Exception as e:
        logging.error(e)


def handle_exception(self, exception):
    logging.exception(exception)
    logging.error("Ha ocurrido un error con la llamada a Telegram. Se reintenta la conexión")
    print("Ha ocurrido un error con la llamada a Telegram. Se reintenta la conexión")
    bot.polling(none_stop=True, timeout=3000)


# INI Actualización de db a partir de la librería de Telegram
# bot = telebot.TeleBot(TOKEN, exception_handler=handle_exception)
bot = telebot.TeleBot(TOKEN)
cs = ChatSearch()

@bot.message_handler(commands=['start', 'help', 'menu', 's', 'h', 'm'])
def send_test(message):
    inicio(message)


@bot.callback_query_handler(lambda call: call.data == "añadir")
def process_callback_añadir(call):
    añadir(call)


@bot.callback_query_handler(lambda call: call.data == "listar")
def process_callback_listar(call):
    listar(call)


@bot.callback_query_handler(lambda call: call.data == "borrar")
def process_callback_borrar(call):
    borrar(call)


def inicio(call):
    boton_añadir = types.InlineKeyboardButton('Añadir', callback_data='añadir')
    boton_listar = types.InlineKeyboardButton('Listar', callback_data='listar')
    boton_borrar = types.InlineKeyboardButton('Borrar', callback_data='borrar')

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(boton_añadir, boton_listar)
    keyboard.row(boton_borrar)

    bot.send_message(call.chat.id, text='Selecciona una acción a realizar', reply_markup=keyboard)


def añadir(call):
    busqueda = bot.send_message(call.message.chat.id,  'Introduce la busqueda:')
    bot.register_next_step_handler(busqueda, guardarBusqueda)


def guardarBusqueda(message):
    cs.chat_id = message.chat.id
    cs.kws = message.text

    rangoPrecio = bot.send_message(message.chat.id,  'Introduce el rango de precio (min-max):')
    bot.register_next_step_handler(rangoPrecio, guardarRangoPrecio)


def guardarRangoPrecio(message):
    rango = message.text.split('-')
    cs.min_price = rango[0].strip()
    if len(rango) > 1:
        cs.max_price = rango[1].strip()

    cs.username = message.from_user.username
    cs.name = message.from_user.first_name
    cs.active = 1

    data = get_categories(URL_CATEGORIES)
    keyboard = types.InlineKeyboardMarkup()

    boton = types.InlineKeyboardButton("Todos" , callback_data='categoria,' + "all")
    keyboard.add(boton)

    for categoria in data['categories']:
        boton = types.InlineKeyboardButton(str(categoria['name']), callback_data='categoria,' + str(categoria['id']))
        keyboard.add(boton)

    bot.send_message(message.chat.id, text='Selecciona una categoria', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    catAux = call.data.split(',')
    if catAux[0] == "categoria":
        categoriaId = catAux[1]
        call.message.text = categoriaId
        guardarCategoria(call)


def guardarCategoria(call):
    if call.message.text == 'all':
        cs.cat_ids = None
    else:
        cs.cat_ids = call.message.text

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    cs.publish_date = fecha
    logging.info('%s', cs)
    db.add_search(cs)
    bot.send_message(call.message.chat.id, "Busqueda guardada")


def borrar(call):
    busquedaBorrar = bot.send_message(call.message.chat.id,  'Introduce la busqueda a borrar:')
    bot.register_next_step_handler(busquedaBorrar, borrarBusqueda)


def borrarBusqueda(call):
    db.del_chat_search(call.chat.id, call.text)
    bot.send_message(call.chat.id, "Busqueda borrada")


def listar(call):
    json = get_categories(URL_CATEGORIES)
    cont = 1

    text = ICON_ARROW + ' <b>Lista de productos en seguimiento:</b>\n'
    
    for chat_search in db.get_chat_searchs(call.message.chat.id):
        if len(text) > 0:
            text += '\n'
        text += "<b>" + str(cont) + ". Busqueda:</b> " + chat_search.kws
        text += '\n'

        if chat_search.min_price is not None:
            text += "<b>Rango precio:</b> " + chat_search.min_price
        text += '-'
        if chat_search.max_price is not None:
            text += chat_search.max_price + "€"
        else:
            text += "€"

        text += '\n'

        if chat_search.cat_ids is not None:
            idCategoria = int(chat_search.cat_ids)

            for categoria in json['categories']:
                if categoria['id'] == idCategoria:
                    categoria = "<b>Categoria:</b> " + categoria['name']
                    text += categoria
                    break
        else:
            text += "<b>Categoria:</b> Todos"

        text += '\n'
        text += '------------------------------------------------------'
        cont += 1

    if len(text) > 0:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')


# /add búsqueda,min-max,categorías separadas por comas
@bot.message_handler(commands=['add', 'añadir', 'append', 'a'])
def add_search(message):
    cs = ChatSearch()
    cs.chat_id = message.chat.id
    parametros = str(message.text).split(' ', 1)
    if len(parametros) < 2:
        # Solo puso el comando
        return
    token = ' '.join(parametros[1:]).split(',')
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
    db.add_search(cs)


pathlog = 'wallbot.log'
if PROFILE is None:
    pathlog = '/logs/' + pathlog

logging.basicConfig(
    handlers=[RotatingFileHandler(pathlog, maxBytes=1000000, backupCount=10, encoding='utf-8')],
#    filename='wallbot.log',
    level=logging.INFO,
    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')

locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')


# FIN

def wallapop():
    while True:
        # Recupera de db las búsquedas que hay que hacer en wallapop con sus respectivos chats_id
        for search in db.get_chats_searchs():
            u = get_url_list(search)

            # Lanza las búsquedas y notificaciones ...
            get_items(u, search.chat_id)

        time.sleep(60)
        continue


def recovery(times):
    try:
        time.sleep(times)
        logging.info("Conexión a Telegram.")
        print("Conexión a Telegram")
        bot.polling(none_stop=True, timeout=3000)
    except Exception as e:
        logging.error("Ha ocurrido un error con la llamada a Telegram. Se reintenta la conexión", e)
        print("Ha ocurrido un error con la llamada a Telegram. Se reintenta la conexión")
        if times > 16:
            times = 16
        recovery(times*2)


def main():
    print("JanJanJan starting...")
    logging.info("JanJanJan starting...")
    db.setup(readVersion())
    threading.Thread(target=wallapop).start()
    recovery(1)


def readVersion():
    file = open("VERSION", "r")
    version = file.readline()
    logging.info("Version %s", version)
    return version


if __name__ == '__main__':
    main()
