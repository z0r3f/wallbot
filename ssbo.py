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
from telebot.types import InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton, ChatMember
from telebot.apihelper import ApiTelegramException, ApiException
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

global tecladoCategorias

def notel(chat_id, producto, obs):
    text = ""

    if obs is not None:
        text += ICON_COLLISION__ + ' '
        text += "<b>¡BAJADA DE PRECIO!</b>"
        text += ' ' + ICON_COLLISION__
        text += "\n\n"
    else:
        text += ICON_DIRECT_HIT_

    if producto['flags']['reserved'] == True:
        text += ICON_EXCLAMATION + ' '
        text += "<b>¡LO HAN RESERVADO!</b>"
        text += ' ' + ICON_EXCLAMATION
        text += "\n\n"

    text += ' <b>' + producto['title'] + '</b>'
    text += '\n\n'

    text += "<b>Descripción: </b>" + producto['description']
    text += '\n\n'

    creationDate = datetime.fromtimestamp(producto['creation_date'] / 1000).strftime("%d/%m/%Y %H:%M:%S")
    text += "<b>Fecha de publicación: </b>" + creationDate
    text += '\n\n'

    modificationDate = datetime.fromtimestamp(producto['modification_date'] / 1000).strftime("%d/%m/%Y %H:%M:%S")
    text += "<b>Fecha de modificación: </b>" + modificationDate
    text += '\n\n'

    text += "<b>Ubicación: </b>" + producto['location']['city']
    text += '\n\n'

    text += "<b>Precio: </b>" + locale.currency(producto['price'], grouping=True)
    text += '\n\n'

    if obs is not None:
        text += "<b>Precio anterior: </b>" + obs
        text += "\n"

    text += '\n'
    urlAnuncio = 'https://es.wallapop.com/item/' + producto['web_slug']

    image_url = producto['images'][0]['original']
    bot.send_photo(chat_id, image_url, caption=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text='Ir al anuncio', url=urlAnuncio)]]), disable_notification=True)


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
                creationDate = datetime.fromtimestamp(producto['creation_date'] / 1000).strftime("%Y-%m-%d %H:%M:%S")
                db.add_item(producto['id'], chat_id, producto['title'], producto['price'], producto['web_slug'], producto['user']['id'], creationDate)
                notel(chat_id, producto, None)
                logging.info('New: id=%s, price=%s, title=%s', str(producto['id']), locale.currency(producto['price'], grouping=True), producto['title'])
            else:
                # Si está comparar precio...
                money = str(producto['price'])
                value_json = Decimal(sub(r'[^\d.]', '', money))
                value_db = Decimal(sub(r'[^\d.]', '', i.price))
                if value_json < value_db:
                    new_obs = locale.currency(float(i.price), grouping=True)
                    if i.observaciones is not None:
                        new_obs += ' - '
                        new_obs += i.observaciones

                    db.update_item(producto['id'], money, new_obs)

                    creationDate = datetime.fromtimestamp(producto['creation_date'] / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    notel(chat_id, producto, new_obs)
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
                    except ApiTelegramException as e:
                        if e.description == "Forbidden: bot was blocked by the user":
                            logging.info("ATENCION! El usuario {} ha bloqueado el bot. No se le pueden enviar mensajes.".format(message.chat.id))
                    except Exception as e:
                        logging.error(e)
                bot.send_message(CHAT_ID_ADMIN, "Todos los avisos enviados", parse_mode='HTML')


@bot.message_handler(commands=['usuariosbloqueados'])
def buscarUsuarios(message):
    parametros = str(message.text).split(' ', 1)
    if len(parametros) < 2:
        return
    
    token = ' '.join(parametros[1:]).split(',')
    if len(token) < 1:
        return
    
    password  = token[0].strip()

    if password != PASSWORD_AVISO:
        return
    
    try:
        buscarUsuariosBloqueados() 
        bot.send_message(CHAT_ID_ADMIN, "Busqueda de usuarios bloqueados finalizada", parse_mode='HTML')
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
    db.update_user(1, call.chat.id)

    boton_añadir = types.InlineKeyboardButton('Añadir', callback_data='añadir')
    boton_listar = types.InlineKeyboardButton('Listar', callback_data='listar')
    boton_borrar = types.InlineKeyboardButton('Borrar', callback_data='borrar')
    boton_estadi = types.InlineKeyboardButton('Estadisticas', callback_data='estadisticas')

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(boton_añadir, boton_listar)
    keyboard.row(boton_borrar, boton_estadi)

    bot.send_message(call.chat.id, text='Selecciona una acción a realizar', reply_markup=keyboard)


def añadir(call):
    busqueda = bot.send_message(call.message.chat.id, 'Introduce la busqueda:')
    bot.register_next_step_handler(busqueda, guardarBusqueda)


def guardarBusqueda(message):
    if message.text.startswith("/"):
        bot.send_message(message.chat.id, 'La busqueda no puede ser un comando')

        busqueda = bot.send_message(message.chat.id, 'Introduce la busqueda:')
        bot.register_next_step_handler(busqueda, guardarBusqueda)
    else:
        busqueda = db.search_chat_search_by_title(message.text, message.chat.id)

        if busqueda is not None:
            bot.send_message(message.chat.id, 'Esa busqueda ya ha sido registrada')
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
    global tecladoCategorias
    tecladoCategorias = bot.send_message(message.chat.id, text='Selecciona una categoria', reply_markup=teclado)


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

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cs.publish_date = fecha
    logging.info('%s', cs)
    db.add_search(cs)

    global tecladoCategorias
    bot.delete_message(call.message.chat.id, tecladoCategorias.message_id)

    json = get_categories(URL_CATEGORIES)

    try:
        text = ICON_WARNING____ + " <b>Busqueda guardada</b> " + ICON_WARNING____
        text += "\n\n"
        text += "<b>Busqueda: </b>" + cs.kws + "\n"
        if cs.cat_ids != None:
            idCategoria = int(cs.cat_ids)
            nombreCategoria = obtenerNombreCategoriaById(idCategoria, json)
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
            text += "<b>Usuario: </b> @" + cs.username + "\n"
            text += "<b>Nombre: </b>" + cs.name + "\n"
            if cs.cat_ids != None:
                idCategoria = int(cs.cat_ids)
                nombreCategoria = obtenerNombreCategoriaById(idCategoria, json)
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
                nombreCategoria = obtenerNombreCategoriaById(idCategoria, json)
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

        text += ICON_MONEY + " <b>Productos Encontrados Hoy:</b> " + str(estadisticas[0].productos_encontrados_dia)
        text += '\n'

        text += ICON_MONEY + " <b>Productos Encontrados Semana:</b> " + str(estadisticas[0].productos_encontrados_semana)
        text += '\n'

        text += ICON_MONEY + " <b>Productos Encontrados Mes:</b> " + str(estadisticas[0].productos_encontrados_mes)
        text += '\n'

        text += ICON_MONEY + " <b>Productos Encontrados Total:</b> " + str(estadisticas[0].productos_encontrados_total)
        text += '\n'
        
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')


def ayuda(message):
    db.update_user(1, message.chat.id)

    text = "Usa este bot para crear busquedas en Wallapop, y obtener avisos instantaneos de la subida de nuevos productos."
    text += "\n\n"
    text += "Bot creado por @Tamasco69"
    bot.send_message(message.chat.id, text, parse_mode='HTML')


def obtenerNombreCategoriaById(idCategoria, json):
    try:
        for categoria in json['categories']:
            if categoria['id'] == idCategoria:
                return categoria['name']
    except Exception as e:
        logging.error(e)


def buscarUsuariosBloqueados():
    usuarios = db.get_usuarios()

    if len(usuarios) > 0:
        for usuario in usuarios:
            try:
                message = bot.send_message(usuario, 'Hola, este es un mensaje de prueba', disable_notification=True)
                bot.delete_message(usuario, message.message_id)
                print("El mensaje ha sido enviado y borrado: " + str(usuario))
                logging.info("El mensaje ha sido enviado y borrado: " + str(usuario))
            except ApiTelegramException as e:
                logging.error(e)
                if e.description == "Forbidden: bot was blocked by the user" or e.description == "Bad Request: chat not found":
                    text = "ATENCION! El usuario {} ha bloqueado el bot. No se le pueden enviar mensajes.".format(usuario)
                    logging.info(text)
                    bot.send_message(CHAT_ID_ADMIN, text, parse_mode='HTML')
                    db.update_user(0, usuario)
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
            url = get_url_list(search)
            # Lanza las búsquedas y notificaciones
            get_items(url, search.chat_id)

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
    print("Wallbot starting...")
    logging.info("Wallbot starting...")
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
