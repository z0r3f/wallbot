import logging
import sqlite3
import time
from pathlib import Path
from typing import List

from src.wallbot.config.settings import PROFILE
from src.wallbot.database.models import ChatSearch, Item


class DBHelper:
    def __init__(self, dbname=None):
        calculated_db_name = self.__get_db_name(dbname)
        logging.info(f"DB: {calculated_db_name}")
        self.__conn = sqlite3.connect(calculated_db_name, check_same_thread=False)

    @staticmethod
    def __get_db_name(dbname=None) -> str:
        if dbname is None:
            if PROFILE is None:
                dbname = "/data/db.sqlite"
            else:
                current_file = Path(__file__)
                project_root = current_file.parent.parent.parent.parent
                dbname = str(project_root / "db.sqlite")
        return dbname

    def setup(self, version=""):
        tblstmtitem = "create table if not exists item " \
                      "(itemId integer, " \
                      "chatId text, " \
                      "title text, " \
                      "price text, " \
                      "url text, " \
                      "user text, " \
                      "publishDate integer, " \
                      "observaciones text, " \
                      "item text, " \
                      " primary key (itemId,chatId))"
        self.__conn.execute(tblstmtitem)

        tblstmtchat = "create table if not exists chat_search " \
                      "(chat_id text, " \
                      "kws text, " \
                      "cat_ids text, " \
                      "min_price text, " \
                      "max_price text, " \
                      "dist text default \'400\', " \
                      "publish_date integer default 24, " \
                      "ord text default \'newest\', " \
                      "username text, " \
                      "name text, " \
                      "active int default 1)"
        self.__conn.execute(tblstmtchat)

        if version == '1.0.6':
            stmt = "update chat_search " \
                   "set ord = \'newest\' " \
                   "where ord = \'creationDate-des\'"
            try:
                self.__conn.execute(stmt)
                self.__conn.commit()
            except Exception as e:
                logging.error(f"Error setting up the db: {e}")

        self.__conn.commit()

    def add_search(self, chat_search):
        stmt = "insert into chat_search (chat_id, kws"
        valu = " values (?, ?"
        args = (chat_search.chat_id, chat_search.kws)
        if chat_search.cat_ids is not None:
            stmt += ", cat_ids"
            valu += ", ?"
            args += (chat_search.cat_ids,)
        if chat_search.min_price is not None:
            stmt += ", min_price"
            valu += ", ?"
            args += (chat_search.min_price,)
        if chat_search.max_price is not None:
            stmt += ", max_price"
            valu += ", ?"
            args += (chat_search.max_price,)
        if chat_search.dist is not None:
            stmt += ", dist"
            valu += ", ?"
            args += (chat_search.dist,)
        if chat_search.publish_date is not None:
            stmt += ", publish_date"
            valu += ", ?"
            args += (chat_search.publish_date,)
        if chat_search.orde is not None:
            stmt += ", ord"
            valu += ", ?"
            args += (chat_search.orde,)
        if chat_search.username is not None:
            stmt += ", username"
            valu += ", ?"
            args += (chat_search.username,)
        if chat_search.name is not None:
            stmt += ", name"
            valu += ", ?"
            args += (chat_search.name,)
        if chat_search.active is not None:
            stmt += ", active"
            valu += ", ?"
            args += (chat_search.active,)
        stmt += ")" + valu + ")"
        try:
            self.__conn.execute(stmt, args)
            self.__conn.commit()
        except sqlite3.IntegrityError as e:
            logging.error(f"Error adding chat search: {e}")

    def add_item(self, item_id, chat_id, title, price, url, user, publish_date=None, observaciones=None):
        stmt = "insert into item (itemId, chatId, title, price, url, user, publishDate, observaciones) " \
               "values (?, ?, ?, ?, ?, ?, ?, ?)"
        args = (item_id, chat_id, title, price, url, user, publish_date, observaciones)
        try:
            self.__conn.execute(stmt, args)
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error adding item: {e}")

    def update_item(self, item_id, price, obs):
        stmt = "update item " \
               "set price = ?, " \
               "observaciones = ? " \
               "where itemId = ?"
        try:
            self.__conn.execute(stmt, (price, obs, item_id))
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error updating item: {e}")

    def delete_items(self, hours_live):
        millis = int(round(time.time() * 1000))
        millis -= hours_live * 60 * 60 * 1000
        stmt = "delete from item where publishDate < (?)"
        args = (millis,)
        try:
            self.__conn.execute(stmt, args)
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error deleting items older than {hours_live} hours: {e}")

    def search_item(self, item_id, chat_id):
        stmt = "select itemId, chatId, title, price, url, publishDate, observaciones, user " \
               "from item where itemId = (?) and chatId = (?)"
        args = (item_id, chat_id)
        try:
            for row in self.__conn.execute(stmt, args):
                i = Item(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
                return i
        except Exception as e:
            logging.error(f"Error searching item: {e}")
        return None

    def get_chat_searches(self, chat_id):
        stmt = "select chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord from chat_search " \
               "where chat_id = ? and active = 1"
        searches = []
        try:
            for row in self.__conn.execute(stmt, (chat_id,)):
                c = ChatSearch(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
                searches.append(c)
        except Exception as e:
            logging.error(f"Error getting chat searches for chat_id {chat_id}: {e}")
        return searches

    def get_chats_searches(self):
        stmt = "select chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord from chat_search " \
               "where active = 1"
        lista: List[ChatSearch] = []
        try:
            for row in self.__conn.execute(stmt):
                c = ChatSearch(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
                lista.append(c)
        except Exception as e:
            logging.error(f"Error getting all chat searches: {e}")

            for i in lista:
                logging.debug(f"Chat: {i.chat_id} - Keywords: {i.kws} - Categories: {i.cat_ids} - "
                              f"Min price: {i.min_price} - Max price: {i.max_price} - "
                              f"Distance: {i.dist} - Publish date: {i.publish_date} - Order: {i.orde}")

        return lista

    def del_chat_search(self, chat_id, kws):
        stmt = "update chat_search set active = 0 where chat_id = ? and kws = ?"
        try:
            self.__conn.execute(stmt, (chat_id, kws))
            self.__conn.commit()
        except Exception as e:
            logging.error(f"Error deleting chat search for chat_id {chat_id} and kws {kws}: {e}")
