import locale
import logging
import time
from typing import Any, Dict, List

from src.wallbot.config.constants import SEARCH_INTERVAL
from src.wallbot.database.db_helper import DBHelper
from src.wallbot.database.models import ChatSearch, Item
from src.wallbot.telegram.notifications import notel
from src.wallbot.wallapop.api_client import WallapopClient


def _format_currency(value: Any) -> str:
    try:
        return locale.currency(float(value), grouping=True)
    except (ValueError, TypeError):
        return f"{value} €"


class WallapopMonitor:
    def __init__(self, db: DBHelper):
        self.db = db
        self.client = WallapopClient()
        self.is_running = False

    def start(self):
        self.is_running = True
        logging.info("Iniciando monitoreo continuo de Wallapop...")

        while self.is_running:
            try:
                self._monitor_cycle()
            except Exception as e:
                logging.error("Error inesperado en ciclo de monitoreo: %s", e)

            # Pausa antes del siguiente escaneo completo
            time.sleep(SEARCH_INTERVAL)

    def stop(self):
        self.is_running = False
        logging.info("Monitoreo detenido")

    def _monitor_cycle(self):
        searches: List[ChatSearch] = self.db.get_chats_searches()
        if not searches:
            return

        for search in searches:
            if not self.is_running:
                break

            try:
                response = self.client.search_items(search)
                if response:
                    self._handle_response(search, response)
            except Exception as e:
                logging.error("Error procesando búsqueda '%s' para chat %s: %s", search.kws, search.chat_id, e)

            # Pequeño retardo entre cada búsqueda para no saturar la API
            time.sleep(1.5)

    def _handle_response(self, search: ChatSearch, response: Dict[str, Any]):
        try:
            # Estructura típica de items en API v3
            items = (
                response.get("data", {})
                .get("section", {})
                .get("payload", {})
                .get("items", [])
            )

            for item in items:
                # Saltar items publicitarios o sin ID
                if not item.get("id"):
                    continue
                self._process_item(item, str(search.chat_id))

        except Exception as e:
            logging.error("Error extrayendo items de la respuesta: %s", e)

    def _process_item(self, item: Dict[str, Any], chat_id: str):
        item_id = item["id"]
        
        # Extracción segura de precio
        price_info = item.get("price", {})
        item_price = price_info.get("amount") if isinstance(price_info, dict) else item.get("price")
        if item_price is None:
            return

        item_title = item.get("title", "Sin título")
        item_user = item.get("user_id", "")
        item_web_slug = item.get("web_slug", str(item_id))

        logging.debug(
            "Item encontrado: id=%s, price=%s, title=%s",
            item_id,
            _format_currency(item_price),
            item_title,
        )

        existing_item = self.db.search_item(item_id, chat_id)

        if existing_item is None:
            self._process_new_item(item_id, chat_id, item_title, item_price, item_web_slug, item_user)
        else:
            self._process_price_update(existing_item, item_id, item_price, item_title, item_web_slug, chat_id)

    def _process_new_item(self, item_id: int, chat_id: str, title: str, price: Any, web_slug: str, user_id: str):
        self.db.add_item(item_id, chat_id, title, str(price), web_slug, user_id)
        notel(chat_id, price, title, web_slug)
        logging.info(
            "NUEVO ANUNCIO: id=%s, price=%s, title=%s",
            item_id,
            _format_currency(price),
            title,
        )

    def _process_price_update(self, existing: Item, item_id: int, new_price: Any, title: str, web_slug: str, chat_id: str):
        try:
            new_p = float(new_price)
            old_p = float(existing.price)
        except (ValueError, TypeError):
            return

        # Solo notificar y actualizar si el precio ha bajado
        if new_p < old_p:
            price_history = _format_currency(existing.price)
            if existing.observaciones:
                price_history += f" < {existing.observaciones}"

            self.db.update_item(item_id, str(new_price), price_history)
            notel(chat_id, new_price, title, web_slug, f" < {price_history}")

            logging.info(
                "BAJADA DE PRECIO: id=%s, %s -> %s, title=%s",
                item_id,
                _format_currency(old_p),
                _format_currency(new_p),
                title,
            )
