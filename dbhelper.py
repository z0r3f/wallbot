import sqlite3
import time


class ChatSearch:

    def __init__(self, chat_id=None, kws=None, cat_ids=None, min_price=None, max_price=None,
                 dist=None, publish_date=None, orde=None, username=None, name=None, active=None):
        self.chat_id = chat_id
        self.kws = kws
        self.cat_ids = cat_ids
        self.min_price = min_price
        self.max_price = max_price
        self.dist = dist
        self.publish_date = publish_date
        self.orde = orde
        self.username = username
        self.name = name
        self.active = active

    def __str__(self) -> str:
        return "<ChatSearch chat_id:%s kws:%s cat_ids:%s min_price:%s max_price:%s " \
               "dist:%s publish_date:%s orde:%s username:%s name:%s active:%s>" % \
               (self.chat_id, self.kws, self.cat_ids, self.min_price, self.max_price,
                self.dist, self.publish_date, self.orde, self.username, self.name, self.active)


class Item:
    def __init__(self, item_id, chat_id, title, price, url, publish_date, observaciones, item):
        self.item_id = item_id
        self.chat_id = chat_id
        self.title = title
        self.price = price
        self.url = url
        self.publish_date = publish_date
        self.observaciones = observaciones
        self.item = item


class DBHelper:
    def __init__(self, dbname="/data/db.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

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
        self.conn.execute(tblstmtitem)

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
        self.conn.execute(tblstmtchat)

        if version == '1.0.6':
            stmt = "update chat_search " \
                   "set ord = \'newest\' " \
                   "where ord = \'creationDate-des\'"
            try:
                self.conn.execute(stmt)
                self.conn.commit()
            except Exception as e:
                print(e)

        self.conn.commit()

    def add_search(self, chat_search):
        stmt = "insert into chat_search (chat_id, kws"
        valu = " values (?, ?"
        args = (chat_search.chat_id, chat_search.kws)
        if chat_search.cat_ids is not None:
            stmt += ", cat_ids"
            valu += ", ?"
            args += (chat_search.cat_ids, )
        if chat_search.min_price is not None:
            stmt += ", min_price"
            valu += ", ?"
            args += (chat_search.min_price, )
        if chat_search.max_price is not None:
            stmt += ", max_price"
            valu += ", ?"
            args += (chat_search.max_price, )
        if chat_search.dist is not None:
            stmt += ", dist"
            valu += ", ?"
            args += (chat_search.dist, )
        if chat_search.publish_date is not None:
            stmt += ", publish_date"
            valu += ", ?"
            args += (chat_search.publish_date, )
        if chat_search.orde is not None:
            stmt += ", ord"
            valu += ", ?"
            args += (chat_search.orde, )
        if chat_search.username is not None:
            stmt += ", username"
            valu += ", ?"
            args += (chat_search.username, )
        if chat_search.name is not None:
            stmt += ", name"
            valu += ", ?"
            args += (chat_search.name, )
        if chat_search.active is not None:
            stmt += ", active"
            valu += ", ?"
            args += (chat_search.active, )
        stmt += ")" + valu + ")"
        try:
            self.conn.execute(stmt, args)
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(e)

    def add_item(self, item_id, chat_id, title, price, url, user, publish_date=None, observaciones=None):
        stmt = "insert into item (itemId, chatId, title, price, url, user, publishDate, observaciones) " \
               "values (?, ?, ?, ?, ?, ?, ?, ?)"
        args = (item_id, chat_id, title, price, url, user, publish_date, observaciones)
        try:
            self.conn.execute(stmt, args)
            self.conn.commit()
        except Exception as e:
            print(e)

    # Actualiza el precio pero no el campo observaciones
    def update_item(self, item_id, price, obs):
        stmt = "update item " \
                  "set price = ?, " \
                  "observaciones = ? " \
                  "where itemId = ?"
        try:
            self.conn.execute(stmt, (price, obs, item_id))
            self.conn.commit()
        except Exception as e:
            print(e)

    def delete_items(self, hours_live):
        millis = int(round(time.time() * 1000))
        millis -= hours_live*60*60*1000
        stmt = "delete from item where publishDate < (?)"
        args = (millis, )
        try:
            self.conn.execute(stmt, args)
            self.conn.commit()
        except Exception as e:
            print(e)

    def search_item(self, item_id, chat_id):
        stmt = "select itemId, chatId, title, price, url, publishDate, observaciones, user " \
                 "from item where itemId = (?) and chatId = (?)"
        args = (item_id, chat_id)
        try:
            for row in self.conn.execute(stmt, args):
                i = Item(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
                return i
        except Exception as e:
            print(e)
        return None

    def get_chat_searchs(self, chat_id):
        stmt = "select chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord from chat_search " \
                "where chat_id = ? and active = 1"
        lista = []
        try:
            for row in self.conn.execute(stmt, (chat_id, )):
                c = ChatSearch(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
                lista.append(c)
        except Exception as e:
            print(e)
        return lista

    def get_chats_searchs(self):
        stmt = "select chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord from chat_search " \
                "where active = 1"
        lista = []
        try:
            for row in self.conn.execute(stmt):
                c = ChatSearch(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
                lista.append(c)
        except Exception as e:
            print(e)
        return lista

    def del_chat_search(self, chat_id, kws):
        stmt = "update chat_search set active = 0 where chat_id = ? and kws = ?"
        try:
            self.conn.execute(stmt, (chat_id, kws))
            self.conn.commit()
        except Exception as e:
            print(e)
