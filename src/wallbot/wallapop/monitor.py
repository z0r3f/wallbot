import locale
import logging
import time
from decimal import Decimal
from re import sub
from typing import List

from src.wallbot.config.constants import SEARCH_INTERVAL
from src.wallbot.database.models import ChatSearch
from src.wallbot.telegram.notifications import notel
from src.wallbot.wallapop.api_client import WallapopClient


class WallapopMonitor:
    def __init__(self, db):
        """
        Inicializa el monitor de Wallapop

        Args:
            db: Instancia de DBHelper para acceso a la base de datos
        """
        self.db = db
        self.client = WallapopClient()
        self.is_running = False

    def start(self):
        """Inicia el bucle de monitoreo"""
        self.is_running = True
        logging.info("Iniciando monitoreo de Wallapop...")

        while self.is_running:
            try:
                self._monitor_cycle()
                time.sleep(SEARCH_INTERVAL)
            except KeyboardInterrupt:
                logging.info("Deteniendo monitoreo...")
                self.stop()
            except Exception as e:
                logging.error(f"Error en ciclo de monitoreo: {e}")
                time.sleep(SEARCH_INTERVAL)

    def stop(self):
        """Detiene el monitoreo"""
        self.is_running = False
        logging.info("Monitoreo detenido")

    def _monitor_cycle(self):
        """Ejecuta un ciclo completo de monitoreo"""
        searches: List[ChatSearch] = self.db.get_chats_searches()

        for search in searches:
            try:
                response = self.client.search_items(search)
                logging.info(f"Respuesta de API: {response}")
                if response:
                    self._handle_response(search, response)
            except Exception as e:
                logging.error(f"Error procesando búsqueda para chat `{search.chat_id}`: {e}")

    def _handle_response(self, search, response):
        """Procesa la respuesta de la API de Wallapop"""
        try:
            items = response['data']['section']['payload']['items']

            for item in items:
                self._process_item(item, search.chat_id)

        except (KeyError, ValueError) as e:
            logging.error(f"Error procesando respuesta de API: {e}")

    def _process_item(self, item, chat_id):
        """Procesa un item individual"""
        item_id = item['id']
        item_price = item['price']['amount']
        item_title = item['title']
        item_user = item['user_id']
        item_web_slug = item['web_slug']

        logging.info(
            'Encontrado: id=%s, price=%s, title=%s, user=%s',
            str(item_id),
            locale.currency(item_price, grouping=True),
            item_title,
            item_user
        )

        existing_item = self.db.search_item(item_id, chat_id)

        if existing_item is None:
            self._process_new_item(item_id, chat_id, item_title, item_price, item_web_slug, item_user)
        else:
            self._process_price_update(existing_item, item_id, item_price, item_title, item_web_slug, chat_id)

    def _process_new_item(self, item_id, chat_id, title, price, web_slug, user_id):
        """Procesa un item nuevo encontrado"""
        self.db.add_item(item_id, chat_id, title, price, web_slug, user_id)
        notel(chat_id, price, title, web_slug)
        logging.info(
            'New: id=%s, price=%s, title=%s',
            str(item_id),
            locale.currency(price, grouping=True),
            title
        )

    def _process_price_update(self, existing_item, item_id, new_price, title, web_slug, chat_id):
        """Procesa una actualización de precio"""
        # Convertir precios a decimales para comparación
        new_price_decimal = Decimal(sub(r'[^\d.]', '', str(new_price)))
        old_price_decimal = Decimal(sub(r'[^\d.]', '', existing_item.price))

        if new_price_decimal < old_price_decimal:
            # Construir historial de precios
            price_history = locale.currency(existing_item.price, grouping=True)
            if existing_item.observaciones:
                price_history += ' < ' + existing_item.observaciones

            # Actualizar item en base de datos
            self.db.update_item(item_id, str(new_price), price_history)

            # Notificar cambio de precio
            notel(chat_id, new_price, title, web_slug, ' < ' + price_history)

            logging.info(
                'Baja: id=%s, price=%s, title=%s',
                str(item_id),
                locale.currency(new_price, grouping=True),
                title
            )
