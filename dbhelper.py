import sqlite3
import time


class ChatSearch:

    def __init__(self, chat_id=None, kws=None, cat_ids=None, min_price=None, max_price=None,
                 dist=None, publish_date=None, orde=None, username=None, name=None, active=None, user_active=None, exclude_words=None, sub_cat_ids=None):
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
        self.user_active = user_active
        self.exclude_words = exclude_words
        self.sub_cat_ids = sub_cat_ids

    def __str__(self) -> str:
        return "<ChatSearch chat_id:%s kws:%s cat_ids:%s min_price:%s max_price:%s " \
               "dist:%s publish_date:%s orde:%s username:%s name:%s active:%s user_active:%s exclude_words:%s sub_cat_ids:%s>" % \
               (self.chat_id, self.kws, self.cat_ids, self.min_price, self.max_price,
                self.dist, self.publish_date, self.orde, self.username, self.name, self.active, self.user_active, self.exclude_words, self.sub_cat_ids)


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


class Estadisticas:
    def __init__(self, total_usuarios, busquedas_activas, productos_encontrados_dia, productos_encontrados_semana, productos_encontrados_mes, productos_encontrados_total):
        self.total_usuarios = total_usuarios
        self.busquedas_activas = busquedas_activas
        self.productos_encontrados_dia = productos_encontrados_dia
        self.productos_encontrados_semana = productos_encontrados_semana
        self.productos_encontrados_mes = productos_encontrados_mes
        self.productos_encontrados_total = productos_encontrados_total


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
                  "publishDate text, " \
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
                      "publish_date text, " \
                      "ord text default \'newest\', " \
                      "username text, " \
                      "name text, " \
                      "active int default 1," \
                      "user_active int default 1," \
                      "exclude_words text," \
                      "sub_cat_ids text)"
        self.conn.execute(tblstmtchat)
        self.conn.commit()

        if version == '1.1.3':
            stmt = "ALTER TABLE chat_search ADD COLUMN sub_cat_ids text"
            try:
                self.conn.execute(stmt)
                self.conn.commit()
            except Exception as e:
                print(e)

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
        if chat_search.exclude_words is not None:
            stmt += ", exclude_words"
            valu += ", ?"
            args += (chat_search.exclude_words, )
        if chat_search.sub_cat_ids is not None:
            stmt += ", sub_cat_ids"
            valu += ", ?"
            args += (chat_search.sub_cat_ids, )
        
        stmt += ", user_active"
        valu += ", ?"
        args += (1, )

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
    
    def search_chat_search_by_title(self, title, chat_id):
        stmt = "select chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord, username, name, active, user_active, exclude_words, sub_cat_ids " \
                 "from chat_search where kws = (?) and chat_id = (?) and active = 1"
        args = (title, chat_id)
        try:
            for row in self.conn.execute(stmt, args):
                i = ChatSearch(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13])
                return i
        except Exception as e:
            print(e)
        return None
    
    def search_chat_search_by_title_cat_ids(self, title, cat_ids, chat_id):
        stmt = "select chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord, username, name, active, user_active, exclude_words, sub_cat_ids " \
                 "from chat_search where kws = (?) and cat_ids = (?) and chat_id = (?) and active = 1"
        args = (title, cat_ids, chat_id)
        try:
            for row in self.conn.execute(stmt, args):
                i = ChatSearch(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13])
                return i
        except Exception as e:
            print(e)
        return None

    def get_chat_searchs(self, chat_id):
        stmt = "select chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord, username, name, active, user_active, exclude_words, sub_cat_ids from chat_search " \
                "where chat_id = ? and active = 1"
        lista = []
        try:
            for row in self.conn.execute(stmt, (chat_id, )):
                c = ChatSearch(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13])
                lista.append(c)
        except Exception as e:
            print(e)
        return lista

    def get_chats_searchs(self):
        stmt = "select chat_id, kws, cat_ids, min_price, max_price, dist, publish_date, ord, username, name, active, user_active, exclude_words, sub_cat_ids from chat_search " \
                "where active = 1 and user_active = 1"
        lista = []
        try:
            for row in self.conn.execute(stmt):
                c = ChatSearch(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13])
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

    def get_estadisticas(self):
        stmt = "SELECT " \
                "(SELECT COUNT(DISTINCT chat_id) FROM chat_search WHERE user_active = 1) AS total_usuarios," \
                "(SELECT COUNT(chat_id) FROM chat_search WHERE active = 1 and user_active = 1) AS busquedas_activas," \
                "(SELECT COUNT(DISTINCT itemId) FROM item WHERE date(publishDate) = date('now')) AS productos_encontrados_dia," \
                "(SELECT COUNT(DISTINCT itemId) FROM item WHERE date(publishDate) BETWEEN date('now', '-7 days') AND date('now')) AS productos_encontrados_semana," \
                "(SELECT COUNT(DISTINCT itemId) FROM item WHERE date(publishDate) BETWEEN date('now', '-1 month') AND date('now')) AS productos_encontrados_mes," \
                "(SELECT COUNT(DISTINCT itemId) FROM item) AS productos_encontrados_total"
        lista = []
        try:
            for row in self.conn.execute(stmt):
                c = Estadisticas(row[0], row[1], row[2], row[3], row[4], row[5])
                lista.append(c)
        except Exception as e:
            print(e)
        return lista
    
    def get_usuarios(self):
        stmt = "SELECT DISTINCT chat_id FROM chat_search WHERE user_active = 1 "
        lista = []
        try:
            for row in self.conn.execute(stmt):
                lista.append(row[0])
        except Exception as e:
            print(e)
        return lista
    
    def update_user(self, active, chat_id):
        stmt = "update chat_search " \
                  "set user_active = ? " \
                  "where chat_id = ?"
        try:
            self.conn.execute(stmt, (active, chat_id))
            self.conn.commit()
        except Exception as e:
            print(e)