import logging
import sqlite3
import time
from typing import List, Optional

from src.wallbot.config.settings import DATABASE_PATH
from src.wallbot.database.models import ChatSearch, Item


class DBHelper:
    def __init__(self, dbname: Optional[str] = None):
        self.db_path = dbname or DATABASE_PATH
        logging.info("DB: %s", self.db_path)

        # timeout=30 evita bloqueos si dos hilos intentan escribir a la vez
        self.__conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0
        )
        # Habilitar WAL mode para mejorar concurrencia entre hilos
        self.__conn.execute("PRAGMA journal_mode = WAL;")
        self.__conn.execute("PRAGMA synchronous = NORMAL;")

    def setup(self, version: str = ""):
        with self.__conn:
            self.__conn.execute(
                """
                CREATE TABLE IF NOT EXISTS item (
                    itemId INTEGER,
                    chatId TEXT,
                    title TEXT,
                    price TEXT,
                    url TEXT,
                    user TEXT,
                    publishDate INTEGER,
                    observaciones TEXT,
                    item TEXT,
                    PRIMARY KEY (itemId, chatId)
                )
                """
            )
            self.__conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_search (
                    chat_id TEXT,
                    kws TEXT,
                    cat_ids TEXT,
                    min_price TEXT,
                    max_price TEXT,
                    dist TEXT DEFAULT '400',
                    publish_date INTEGER DEFAULT 24,
                    ord TEXT DEFAULT 'newest',
                    username TEXT,
                    name TEXT,
                    active INTEGER DEFAULT 1
                )
                """
            )

    def add_search(self, cs: ChatSearch):
        fields = ["chat_id", "kws"]
        values = [cs.chat_id, cs.kws]

        optional_fields = [
            ("cat_ids", cs.cat_ids),
            ("min_price", cs.min_price),
            ("max_price", cs.max_price),
            ("dist", cs.dist),
            ("publish_date", cs.publish_date),
            ("ord", cs.orde),
            ("username", cs.username),
            ("name", cs.name),
            ("active", cs.active),
        ]

        for col, val in optional_fields:
            if val is not None:
                fields.append(col)
                values.append(val)

        cols_sql = ", ".join(fields)
        placeholders = ", ".join("?" for _ in fields)
        stmt = f"INSERT INTO chat_search ({cols_sql}) VALUES ({placeholders})"

        try:
            with self.__conn:
                self.__conn.execute(stmt, values)
        except sqlite3.Error as e:
            logging.error("Error al añadir búsqueda: %s", e)

    def add_item(self, item_id, chat_id, title, price, url, user, publish_date=None, observaciones=None):
        stmt = """
            INSERT INTO item (itemId, chatId, title, price, url, user, publishDate, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self.__conn:
                self.__conn.execute(stmt, (item_id, chat_id, title, price, url, user, publish_date, observaciones))
        except sqlite3.Error as e:
            logging.error("Error al guardar anuncio %s: %s", item_id, e)

    def update_item(self, item_id, price, obs):
        stmt = "UPDATE item SET price = ?, observaciones = ? WHERE itemId = ?"
        try:
            with self.__conn:
                self.__conn.execute(stmt, (price, obs, item_id))
        except sqlite3.Error as e:
            logging.error("Error al actualizar anuncio %s: %s", item_id, e)

    def delete_items(self, hours_live: int):
        cutoff_millis = int(round(time.time() * 1000)) - (hours_live * 3600 * 1000)
        stmt = "DELETE FROM item WHERE publishDate < ?"
        try:
            with self.__conn:
                self.__conn.execute(stmt, (cutoff_millis,))
        except sqlite3.Error as e:
            logging.error("Error al limpiar anuncios antiguos: %s", e)

    def search_item(self, item_id, chat_id) -> Optional[Item]:
        stmt = """
            SELECT itemId, chatId, title, price, url, publishDate, observaciones, user
            FROM item WHERE itemId = ? AND chatId = ?
        """
        try:
            cursor = self.__conn.cursor()
            cursor.execute(stmt, (item_id, chat_id))
            row = cursor.fetchone()
            if row:
                return Item(
                    item_id=row[0],
                    chat_id=row[1],
                    title=row[2],
                    price=row[3],
                    url=row[4],
                    publish_date=row[5],
                    observaciones=row[6],
                    user=row[7]
                )
        except sqlite3.Error as e:
            logging.error("Error al consultar anuncio %s: %s", item_id, e)
        return None

    def get_chat_searches(self, chat_id) -> List[ChatSearch]:
        stmt = """
            SELECT chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord
            FROM chat_search WHERE chat_id = ? AND active = 1
        """
        searches = []
        try:
            cursor = self.__conn.cursor()
            cursor.execute(stmt, (chat_id,))
            for row in cursor.fetchall():
                searches.append(ChatSearch(
                    chat_id=row[0], kws=row[1], cat_ids=row[2],
                    min_price=row[3], max_price=row[4], dist=row[5],
                    publish_date=row[6], orde=row[7]
                ))
        except sqlite3.Error as e:
            logging.error("Error al obtener búsquedas de chat %s: %s", chat_id, e)
        return searches

    def get_chats_searches(self) -> List[ChatSearch]:
        stmt = """
            SELECT chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord
            FROM chat_search WHERE active = 1
        """
        lista: List[ChatSearch] = []
        try:
            cursor = self.__conn.cursor()
            cursor.execute(stmt)
            for row in cursor.fetchall():
                lista.append(ChatSearch(
                    chat_id=row[0], kws=row[1], cat_ids=row[2],
                    min_price=row[3], max_price=row[4], dist=row[5],
                    publish_date=row[6], orde=row[7]
                ))
        except sqlite3.Error as e:
            logging.error("Error al obtener todas las búsquedas activas: %s", e)
        return lista

    def del_chat_search(self, chat_id, kws):
        stmt = "UPDATE chat_search SET active = 0 WHERE chat_id = ? AND kws = ?"
        try:
            with self.__conn:
                self.__conn.execute(stmt, (chat_id, kws))
        except sqlite3.Error as e:
            logging.error("Error al desactivar búsqueda '%s' para chat %s: %s", kws, chat_id, e)
