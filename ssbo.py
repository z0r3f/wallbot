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
PASSWORD_AVISO = os.getenv("PASSWORD_AVISO")
CHAT_ID_ADMIN = os.getenv("CHAT_ID_ADMIN")

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
ICON_BAR_CHART   = u'\U0001F4CA'  # 📊
ICON_MAGNIFYING  = u'\U0001F50E'  # 🔎
ICON_USER        = u'\U0001F464'  # 👤
ICON_MONEY       = u'\U0001F4B8'  # 💸


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

            # Borrar fotos productos
            borrarFotos()

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

@bot.message_handler(commands=['start', 'menu', 's', 'm'])
def send_test(message):
    inicio(message)


@bot.message_handler(commands=['help', 'h'])
def send_test(message):
    ayuda(message)


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


@bot.message_handler(commands=['aviso'])
def enviarAviso(message):
    parametros = str(message.text).split(' ', 1)
    if len(parametros) < 2:
        return
    
    token = ' '.join(parametros[1:]).split(',')
    if len(token) < 1:
        return
    
    password  = token[0].strip()

    if password != PASSWORD_AVISO:
        return
    
    if len(token) > 1:
        aviso  = token[1].strip()

        if len(aviso) > 2:
            usuarios = db.get_usuarios()

            if len(usuarios) > 0:
                for usuario in usuarios:
                    try:
                        bot.send_message(usuario, aviso, parse_mode='HTML')
                        text = "Aviso enviado a: " + str(usuario)
                        bot.send_message(CHAT_ID_ADMIN, text, parse_mode='HTML')
                    except Exception as e:
                        logging.error(e)


@bot.callback_query_handler(lambda call: call.data == "añadir")
def process_callback_añadir(call):
    añadir(call)


@bot.callback_query_handler(lambda call: call.data == "listar")
def process_callback_listar(call):
    listar(call)


@bot.callback_query_handler(lambda call: call.data == "borrar")
def process_callback_borrar(call):
    borrar(call)


@bot.callback_query_handler(lambda call: call.data == "estadisticas")
def process_callback_estadisticas(call):
    estadisticas(call)


def inicio(call):
    boton_añadir = types.InlineKeyboardButton('Añadir', callback_data='añadir')
    boton_listar = types.InlineKeyboardButton('Listar', callback_data='listar')
    boton_borrar = types.InlineKeyboardButton('Borrar', callback_data='borrar')
    boton_estadi = types.InlineKeyboardButton('Estadisticas', callback_data='estadisticas')

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(boton_añadir, boton_listar)
    keyboard.row(boton_borrar, boton_estadi)

    bot.send_message(call.chat.id, text='Selecciona una acción a realizar', reply_markup=keyboard)


def añadir(call):
    busqueda = bot.send_message(call.message.chat.id,  'Introduce la busqueda:')
    bot.register_next_step_handler(busqueda, guardarBusqueda)


def guardarBusqueda(message):
    busqueda = db.search_chat_search_by_title(message.text, message.chat.id)

    if busqueda is not None:
        bot.send_message(message.chat.id,  'Esa busqueda ya ha sido registrada')
    else:
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

    # Crear las filas de botones
    filas = []
    fila_actual = []
    for categoria in data['categories']:
        boton = telebot.types.InlineKeyboardButton(str(categoria['name']), callback_data='categoria,' + str(categoria['id']))
        fila_actual.append(boton)
        if len(fila_actual) == 3:
            filas.append(fila_actual)
            fila_actual = []

    # Comprobar si hay una fila parcial al final
    if fila_actual:
        filas.append(fila_actual)

    # Crear el teclado con las filas
    teclado = telebot.types.InlineKeyboardMarkup()

    boton = types.InlineKeyboardButton("Todos" , callback_data='categoria,' + "all")
    teclado.add(boton)

    for fila in filas:
        teclado.row(*fila)

    # Enviar el teclado al usuario
    bot.send_message(message.chat.id, text='Selecciona una categoria', reply_markup=teclado)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    catAux = call.data.split(',')
    if catAux[0] == "categoria":
        categoriaId = catAux[1]
        call.message.text = categoriaId
        guardarCategoria(call)
    elif catAux[0] == "id":
        chatId = catAux[1]
        id = catAux[2]
        borrarBusqueda(chatId, id)


def guardarCategoria(call):
    if call.message.text == 'all':
        cs.cat_ids = None
    else:
        cs.cat_ids = call.message.text

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    cs.publish_date = fecha
    logging.info('%s', cs)
    db.add_search(cs)

    try:
        text = ICON_WARNING____ + " <b>Busqueda guardada</b> " + ICON_WARNING____
        text += "\n\n"
        text += "<b>Busqueda: </b>" + cs.kws + "\n"
        if cs.cat_ids != None:
            idCategoria = int(cs.cat_ids)
            nombreCategoria = obtenerNombreCategoriaById(idCategoria)
            text += "<b>Categoria: </b>" + nombreCategoria + "\n"
        else:
            text += "<b>Categoria: </b> Todos\n"
        text += "<b>Precio Minimo: </b>" + cs.min_price + "\n"
        text += "<b>Precio Maximo: </b>" + cs.max_price + "\n"

        bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    except Exception as e:
        logging.error(e)

    if call.message.chat.id != CHAT_ID_ADMIN:
        try:
            text = ICON_WARNING____ + " <b>Nuevo Registro</b> " + ICON_WARNING____
            text += "\n\n"
            text += "<b>Busqueda: </b>" + cs.kws + "\n"
            text += "<b>Usuario: </b>" + cs.username + "\n"
            text += "<b>Nombre: </b>" + cs.name + "\n"
            if cs.cat_ids != None:
                idCategoria = int(cs.cat_ids)
                nombreCategoria = obtenerNombreCategoriaById(idCategoria)
                text += "<b>Categoria: </b>" + nombreCategoria + "\n"
            else:
                text += "<b>Categoria: </b> Todos\n"
            text += "<b>Precio Minimo: </b>" + cs.min_price + "\n"
            text += "<b>Precio Maximo: </b>" + cs.max_price + "\n"

            bot.send_message(CHAT_ID_ADMIN, text, parse_mode="HTML")
        except Exception as e:
            logging.error(e)


def borrar(call):
    busquedas = db.get_chat_searchs(call.message.chat.id)
    
    if len(busquedas) == 0:
        text = '<b>No hay ninguna busqueda para borrar</b>\n'
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    else:    
        keyboard = types.InlineKeyboardMarkup()
        for busqueda in busquedas:
            boton = types.InlineKeyboardButton(busqueda.kws, callback_data='id,' + str(call.message.chat.id) + ',' + busqueda.kws)
            keyboard.add(boton) 

        bot.send_message(call.message.chat.id, text='Escoge que producto quieres borrar', reply_markup=keyboard)


def borrarBusqueda(chatId, text):
    db.del_chat_search(chatId, text)
    bot.send_message(chatId, "Busqueda borrada")


def listar(call):
    busquedas = db.get_chat_searchs(call.message.chat.id)

    if len(busquedas) == 0:
        text = '<b>No hay ninguna busqueda creada</b>\n'
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    else:
        json = get_categories(URL_CATEGORIES)
        cont = 1

        text = ICON_ARROW + ' <b>Lista de productos en seguimiento:</b>\n'
        
        for busqueda in busquedas:
            if len(text) > 0:
                text += '\n'
            text += "<b>" + str(cont) + ". Busqueda:</b> " + busqueda.kws
            text += '\n'

            if busqueda.min_price is not None:
                text += "<b>Rango precio:</b> " + busqueda.min_price
            text += '-'
            if busqueda.max_price is not None:
                text += busqueda.max_price + "€"
            else:
                text += "€"

            text += '\n'

            if busqueda.cat_ids is not None:
                idCategoria = int(busqueda.cat_ids)
                nombreCategoria = obtenerNombreCategoriaById(idCategoria)
                categoria = "<b>Categoria:</b> " + nombreCategoria
                text += categoria
            else:
                text += "<b>Categoria:</b> Todos"

            text += '\n'
            text += '------------------------------------------------------'
            cont += 1

        bot.send_message(call.message.chat.id, text, parse_mode='HTML')


def estadisticas(call):
    estadisticas = db.get_estadisticas()

    if len(estadisticas) == 0:
        text = '<b>No hay estadisticas</b>\n'
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    else:
        text = ICON_BAR_CHART + ' <b>Estadisticas: </b>\n'

        text += ICON_USER + " <b>Total Usuarios:</b> " + str(estadisticas[0].total_usuarios)
        text += '\n'

        text += ICON_MAGNIFYING + " <b>Busquedas Activas:</b> " + str(estadisticas[0].busquedas_activas)
        text += '\n'

        text += ICON_MONEY + " <b>Productos Encontrados:</b> " + str(estadisticas[0].productos_encontrados)
        text += '\n'
        
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')


def ayuda(message):
    text = "Usa este bot para crear busquedas en Wallapop, y obtener avisos instantaneos de la subida de nuevos productos."
    text += "\n\n"
    text += "Bot creado por @Tamasco69"
    bot.send_message(message.chat.id, text, parse_mode='HTML')


def borrarFotos():
    folder_path = '/data/media'
    photo_extensions = ['.jpg', '.jpeg', '.png', '.gif']  # Extensiones de archivo de las fotos
    file_list = os.listdir(folder_path)
    photo_list = [file for file in file_list if os.path.splitext(file)[1].lower() in photo_extensions]

    for photo in photo_list:
        try:
            photo_path = os.path.join(folder_path, photo)
            os.remove(photo_path)
        except Exception as e:
            logging.error(e)


def obtenerNombreCategoriaById(idCategoria):
    try:
        json = get_categories(URL_CATEGORIES)

        for categoria in json['categories']:
            if categoria['id'] == idCategoria:
                return categoria['name']
    except Exception as e:
        logging.error(e)


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
