import logging
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from src.wallbot.config.settings import WALLAPOP_API_URL
from src.wallbot.database.models import ChatSearch


class WallapopClient:
    def __init__(self):
        self.base_url = WALLAPOP_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "x-deviceos": "0",
        })

    def search_items(self, search: ChatSearch) -> Optional[Dict[str, Any]]:
        params = {
            "source": "search_box",
            "keywords": search.kws or "",
            "time_filter": "today",
        }

        if search.cat_ids:
            params["category_ids"] = search.cat_ids
        if search.min_price is not None:
            params["min_sale_price"] = str(search.min_price)
        if search.max_price is not None:
            params["max_sale_price"] = str(search.max_price)
        if search.dist:
            params["dist"] = str(search.dist)
        if search.orde:
            params["order_by"] = search.orde

        query_string = urlencode(params)
        full_url = f"{self.base_url}?{query_string}"
        logging.debug("API Wallapop ->: %s", full_url)

        try:
            response = self.session.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            logging.debug("API Wallapop <-: %s", data)
            return data
        except requests.RequestException as e:
            logging.error("Error en petición a API Wallapop (%s): %s", search.kws, e)
            return None
