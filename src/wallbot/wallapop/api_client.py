import logging

import requests

from src.wallbot.config.settings import WALLAPOP_API_URL
from src.wallbot.database.models import ChatSearch


class WallapopClient:
    def __init__(self):
        self.base_url = WALLAPOP_API_URL
        self.headers = {'x-deviceos': '0'}

    def search_items(self, search: ChatSearch):
        url = self._build_search_url(search)
        logging.debug(f"API Wallapop ->: {url}")
        try:
            response = requests.get(url=url, headers=self.headers)
            response.raise_for_status()
            logging.debug(f"API Wallapop <-: {response.json()}")
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error en API Wallapop: {e}")
            return None

    def _build_search_url(self, search):
        url = f"{self.base_url}?source=search_box"
        url += f"&keywords={'+'.join(search.kws.split(' '))}"
        url += "&time_filter=today"

        if search.cat_ids:
            url += f"&category_ids={search.cat_ids}"
        if search.min_price:
            url += f"&min_sale_price={search.min_price}"
        if search.max_price:
            url += f"&max_sale_price={search.max_price}"
        if search.dist:
            url += f"&dist={search.dist}"
        if search.orde:
            url += f"&order_by={search.orde}"

        return url
