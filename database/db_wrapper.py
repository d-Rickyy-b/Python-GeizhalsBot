# -*- coding: utf-8 -*-
import logging
import os
import sqlite3
from datetime import datetime

from bot.user import User
from geizhals import Product, Wishlist

__author__ = 'Rico'


class DBwrapper(object):
    class __DBwrapper(object):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        logger = logging.getLogger(__name__)

        def __init__(self, db_name="users.db"):
            database_path = os.path.join(self.dir_path, db_name)

            self.connection = None
            self.cursor = None

            self.create_database(database_path)
            self.setup_connection(database_path)
            self.create_tables()

        def delete_all_tables(self):
            self.logger.info("Dropping all tables!")
            self.cursor.execute("DROP TABLE IF EXISTS wishlist_subscribers;")
            self.cursor.execute("DROP TABLE IF EXISTS product_subscribers;")
            self.cursor.execute("DROP TABLE IF EXISTS wishlist_prices;")
            self.cursor.execute("DROP TABLE IF EXISTS product_prices;")
            self.cursor.execute("DROP TABLE IF EXISTS wishlists;")
            self.cursor.execute("DROP TABLE IF EXISTS products;")
            self.cursor.execute("DROP TABLE IF EXISTS users;")
            self.connection.commit()
            self.logger.info("Dropping complete!")

        def create_database(self, database_path):
            """Create database file and add admin and users table to the database"""
            if not os.path.exists(database_path):
                self.logger.info("File '{}' does not exist! Trying to create one.".format(database_path))
                try:
                    open(database_path, 'a').close()
                except Exception as e:
                    self.logger.error("An error has occurred while creating the database!")
                    self.logger.error(e)

        def create_tables(self):
            """Creates all the tables of the database, if they don't exist"""
            self.logger.info("Creating tables!")

            self.cursor.execute("CREATE TABLE IF NOT EXISTS 'users' \
                                       ('user_id' INTEGER NOT NULL PRIMARY KEY UNIQUE, \
                                       'first_name' TEXT, \
                                       'username' TEXT, \
                                       'lang_code' TEXT NOT NULL DEFAULT 'en_US');")

            self.cursor.execute("CREATE TABLE IF NOT EXISTS 'products' \
                                       ('product_id' INTEGER NOT NULL PRIMARY KEY UNIQUE, \
                                       'name' TEXT NOT NULL DEFAULT 'No title', \
                                       'price' REAL NOT NULL DEFAULT 0, \
                                       'url' TEXT NOT NULL);")

            self.cursor.execute("CREATE TABLE IF NOT EXISTS 'wishlists' \
                                       ('wishlist_id' INTEGER NOT NULL PRIMARY KEY UNIQUE, \
                                       'name' TEXT NOT NULL DEFAULT 'No title', \
                                       'price' REAL NOT NULL DEFAULT 0, \
                                       'url' TEXT NOT NULL);")

            self.cursor.execute("CREATE TABLE IF NOT EXISTS 'product_prices' \
                                       ('product_id' INTEGER NOT NULL, \
                                       'price' REAL NOT NULL DEFAULT 0, \
                                       'timestamp' INTEGER NOT NULL DEFAULT 0, \
                                       FOREIGN KEY('product_id') REFERENCES products(product_id) ON DELETE CASCADE ON UPDATE CASCADE);")

            self.cursor.execute("CREATE TABLE IF NOT EXISTS 'wishlist_prices' \
                                       ('wishlist_id' INTEGER NOT NULL, \
                                       'price' REAL NOT NULL DEFAULT 0, \
                                       'timestamp' INTEGER NOT NULL DEFAULT 0, \
                                       FOREIGN KEY('wishlist_id') REFERENCES wishlists(wishlist_id) ON DELETE CASCADE ON UPDATE CASCADE);")

            self.cursor.execute("CREATE TABLE IF NOT EXISTS 'product_subscribers' \
                                       ('product_id' INTEGER NOT NULL, \
                                       'user_id' INTEGER NOT NULL, \
                                       FOREIGN KEY('product_id') REFERENCES products(product_id) ON DELETE CASCADE ON UPDATE CASCADE,\
                                       FOREIGN KEY('user_id') REFERENCES users(user_id) ON DELETE CASCADE);")

            self.cursor.execute("CREATE TABLE IF NOT EXISTS 'wishlist_subscribers' \
                                       ('wishlist_id' INTEGER NOT NULL, \
                                       'user_id' INTEGER NOT NULL, \
                                       FOREIGN KEY('wishlist_id') REFERENCES wishlists(wishlist_id) ON DELETE CASCADE ON UPDATE CASCADE, \
                                       FOREIGN KEY('user_id') REFERENCES users(user_id) ON DELETE CASCADE);")

        def setup_connection(self, database_path):
            self.connection = sqlite3.connect(database_path, check_same_thread=False)
            self.connection.execute("PRAGMA foreign_keys = ON;")
            self.connection.text_factory = lambda x: str(x, 'utf-8', "ignore")
            self.cursor = self.connection.cursor()

        def get_subscribed_wishlist_count(self, user_id):
            self.cursor.execute("SELECT COUNT(*) "
                                "FROM wishlists "
                                "INNER JOIN wishlist_subscribers on wishlist_subscribers.wishlist_id=wishlists.wishlist_id "
                                "WHERE wishlist_subscribers.user_id=?;", [str(user_id)])
            return self.cursor.fetchone()[0]

        def get_subscribed_product_count(self, user_id):
            self.cursor.execute("SELECT COUNT(*) "
                                "FROM products "
                                "INNER JOIN product_subscribers on product_subscribers.product_id=products.product_id "
                                "WHERE product_subscribers.user_id=?;", [str(user_id)])
            return self.cursor.fetchone()[0]

        def get_all_wishlists(self):
            self.cursor.execute("SELECT wishlist_id, name, price, url FROM wishlists;")
            wishlist_l = self.cursor.fetchall()
            wishlists = []

            for line in wishlist_l:
                wishlists.append(Wishlist(id=line[0], name=line[1], price=line[2], url=line[3]))

            return wishlists

        def get_all_subscribed_wishlists(self):
            self.cursor.execute("SELECT w.wishlist_id, name, price, url FROM wishlists w INNER JOIN wishlist_subscribers ws ON ws.wishlist_id=w.wishlist_id GROUP BY w.wishlist_id;")
            wishlist_l = self.cursor.fetchall()
            wishlists = []

            for line in wishlist_l:
                wishlists.append(Wishlist(id=line[0], name=line[1], price=line[2], url=line[3]))

            return wishlists

        def get_all_products(self):
            self.cursor.execute("SELECT product_id, name, price, url FROM products;")
            product_l = self.cursor.fetchall()
            products = []

            for line in product_l:
                products.append(Product(id=line[0], name=line[1], price=line[2], url=line[3]))

            return products

        def get_all_subscribed_products(self):
            self.cursor.execute("SELECT p.product_id, name, price, url FROM products p INNER JOIN product_subscribers ps ON ps.product_id=p.product_id GROUP BY p.product_id;")
            product_l = self.cursor.fetchall()
            products = []

            for line in product_l:
                products.append(Product(id=line[0], name=line[1], price=line[2], url=line[3]))

            return products

        def get_wishlist_info(self, wishlist_id):
            self.cursor.execute("SELECT wishlist_id, name, price, url FROM wishlists WHERE wishlist_id=?;", [str(wishlist_id)])
            wishlist = self.cursor.fetchone()

            if wishlist is not None:
                wl_id, name, price, url = wishlist
                return Wishlist(id=wl_id, name=name, price=price, url=url)

            return None

        def get_product_info(self, product_id):
            self.cursor.execute("SELECT product_id, name, price, url FROM products WHERE product_id=?;", [str(product_id)])
            product = self.cursor.fetchone()

            if product is None:
                return None

            p_id, name, price, url = product
            return Product(id=p_id, name=name, price=price, url=url)

        def is_wishlist_saved(self, wishlist_id):
            self.cursor.execute("SELECT count(*) FROM wishlists WHERE wishlist_id=?;", [str(wishlist_id)])
            result = self.cursor.fetchone()[0]

            return result > 0

        def is_product_saved(self, product_id):
            self.cursor.execute("SELECT count(*) FROM products WHERE product_id=?;", [str(product_id)])
            result = self.cursor.fetchone()[0]
            return result > 0

        def add_wishlist(self, id, name, price, url):
            self.cursor.execute("INSERT INTO wishlists (wishlist_id, name, price, url) VALUES (?, ?, ?, ?);", [str(id), str(name), str(price), str(url)])
            self.connection.commit()

        def add_product(self, id, name, price, url):
            self.cursor.execute("INSERT INTO products (product_id, name, price, url) VALUES (?, ?, ?, ?);", [str(id), str(name), str(price), str(url)])
            self.connection.commit()

        def rm_wishlist(self, wishlist_id):
            self.cursor.execute("DELETE FROM wishlists WHERE wishlists.wishlist_id=?", [str(wishlist_id)])
            self.connection.commit()

        def rm_product(self, product_id):
            self.cursor.execute("DELETE FROM products WHERE products.product_id=?", [str(product_id)])
            self.connection.commit()

        def subscribe_wishlist(self, wishlist_id, user_id):
            self.cursor.execute("INSERT INTO wishlist_subscribers VALUES (?, ?);", [str(wishlist_id), str(user_id)])
            self.connection.commit()

        def subscribe_product(self, product_id, user_id):
            self.cursor.execute("INSERT INTO product_subscribers VALUES (?, ?);", [str(product_id), str(user_id)])
            self.connection.commit()

        def unsubscribe_wishlist(self, user_id, wishlist_id):
            self.cursor.execute("DELETE FROM wishlist_subscribers WHERE user_id=? and wishlist_id=?;", [str(user_id), str(wishlist_id)])
            self.connection.commit()

        def unsubscribe_product(self, user_id, product_id):
            self.cursor.execute("DELETE FROM product_subscribers WHERE user_id=? and product_id=?;", [str(user_id), str(product_id)])
            self.connection.commit()

        def get_user(self, user_id):
            self.cursor.execute("SELECT user_id, first_name, username, lang_code FROM users WHERE user_id=?;", [str(user_id)])
            user_data = self.cursor.fetchone()
            if user_data:
                return User(id=user_data[0], first_name=user_data[1], username=user_data[2], lang_code=user_data[3])
            return None

        def get_userids_for_wishlist(self, wishlist_id):
            self.cursor.execute("SELECT user_id FROM 'wishlist_subscribers' AS ws "
                                "INNER JOIN wishlists "
                                "ON wishlists.wishlist_id=ws.wishlist_id "
                                "WHERE ws.wishlist_id=?;", [str(wishlist_id)])
            user_list = self.cursor.fetchall()
            user_ids = []

            for line in user_list:
                user_ids.append(line[0])

            return user_ids

        def get_userids_for_product(self, product_id):
            self.cursor.execute("SELECT user_id FROM 'product_subscribers' AS ps "
                                "INNER JOIN products "
                                "ON products.product_id=ps.product_id "
                                "WHERE ps.product_id=?;", [str(product_id)])

            user_list = self.cursor.fetchall()
            user_ids = []

            for line in user_list:
                user_ids.append(line[0])

            return user_ids

        def get_wishlists_for_user(self, user_id):
            """Return all wishlists a user subscribed to"""
            self.cursor.execute(
                "SELECT wishlists.wishlist_id, wishlists.name, wishlists.price, wishlists.url \
                 FROM 'wishlist_subscribers' AS ws \
                 INNER JOIN wishlists on wishlists.wishlist_id=ws.wishlist_id \
                 WHERE ws.user_id=?;", [str(user_id)])
            wishlist_l = self.cursor.fetchall()
            wishlists = []

            for line in wishlist_l:
                wishlists.append(Wishlist(id=line[0], name=line[1], price=line[2], url=line[3]))

            return wishlists

        def get_products_for_user(self, user_id):
            """Returns all products a user subscribed to"""
            self.cursor.execute(
                "SELECT products.product_id, products.name, products.price, products.url \
                 FROM 'product_subscribers' AS ps \
                 INNER JOIN products on products.product_id=ps.product_id \
                 WHERE ps.user_id=?;", [str(user_id)])
            product_l = self.cursor.fetchall()
            products = []

            for line in product_l:
                products.append(Product(id=line[0], name=line[1], price=line[2], url=line[3]))

            return products

        def is_user_wishlist_subscriber(self, user_id, wishlist_id):
            self.cursor.execute("SELECT * FROM wishlist_subscribers AS ws WHERE ws.user_id=? AND ws.wishlist_id=?;", [str(user_id), str(wishlist_id)])
            result = self.cursor.fetchone()
            return result and len(result) > 0

        def is_user_product_subscriber(self, user_id, product_id):
            self.cursor.execute("SELECT * FROM product_subscribers AS ps WHERE ps.user_id=? AND ps.product_id=?;", [str(user_id), str(product_id)])
            result = self.cursor.fetchone()
            return result and len(result) > 0

        def update_wishlist_name(self, wishlist_id, name):
            self.cursor.execute("UPDATE wishlists SET name=? WHERE wishlist_id=?;", [str(name), str(wishlist_id)])
            self.connection.commit()

        def update_product_name(self, product_id, name):
            self.cursor.execute("UPDATE products SET name=? WHERE product_id=?;", [str(name), str(product_id)])
            self.connection.commit()

        def update_wishlist_price(self, wishlist_id, price):
            """Update the price of a wishlist in the database and add a price entry in the wishlist_prices table"""
            self.cursor.execute("UPDATE wishlists SET price=? WHERE wishlist_id=?;", [str(price), str(wishlist_id)])
            try:
                utc_timestamp_now = int(datetime.utcnow().timestamp())
                self.cursor.execute("INSERT INTO wishlist_prices VALUES (?, ?, ?)", [str(wishlist_id), str(price), str(utc_timestamp_now)])
            except sqlite3.IntegrityError:
                self.logger.error("Insert into wishlist_prices not possible: {}, {}".format(wishlist_id, price))
            self.connection.commit()

        def update_product_price(self, product_id, price):
            """Update the price of a product in the database and add a price entry in the product_prices table"""
            self.cursor.execute("UPDATE products SET price=? WHERE product_id=?;", [str(price), str(product_id)])
            try:
                utc_timestamp_now = int(datetime.utcnow().timestamp())
                self.cursor.execute("INSERT INTO product_prices VALUES (?, ?, ?)", [str(product_id), str(price), str(utc_timestamp_now)])
            except sqlite3.IntegrityError:
                self.logger.error("Insert into product_prices not possible: {}, {}".format(product_id, price))
            self.connection.commit()

        def get_all_users(self):
            self.cursor.execute("SELECT user_id, first_name, username, lang_code FROM users;")
            result = self.cursor.fetchall()
            users = []

            if result:
                for user in result:
                    users.append({"id": user[0], "first_name": user[1], "username": user[2], "lang_code": user[3]})

            return users

        def get_lang_id(self, user_id):
            self.cursor.execute("SELECT lang_code FROM users WHERE user_id=?;", [str(user_id)])
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                return "en"

        def add_user(self, user_id, first_name, username, lang_code="de-DE"):
            lang_code = lang_code or "de-DE"
            try:
                self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?);", (str(user_id), str(first_name), str(username), str(lang_code)))
                self.connection.commit()
            except sqlite3.IntegrityError:
                # print("User already exists")
                pass

        def delete_user(self, user_id):
            """Delete a user and remove its subscriptions from the database"""
            try:
                self.cursor.execute("DELETE FROM users WHERE user_id=?;", [user_id])
                self.connection.commit()
            except Exception as e:
                logging.error(e)

        def is_user_saved(self, user_id):
            self.cursor.execute("SELECT rowid, * FROM users WHERE user_id=?;", [str(user_id)])
            result = self.cursor.fetchall()

            if len(result) > 0:
                return True

            return False

        def close_conn(self):
            self.connection.close()

    instance = None

    def __init__(self, db_name="users.db"):
        if not DBwrapper.instance:
            DBwrapper.instance = DBwrapper.__DBwrapper(db_name)

    @staticmethod
    def get_instance(db_name="users.db"):
        if not DBwrapper.instance:
            DBwrapper.instance = DBwrapper.__DBwrapper(db_name)

        return DBwrapper.instance
