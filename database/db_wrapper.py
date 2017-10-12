# -*- coding: utf-8 -*-
import os
import sqlite3
from wishlist import Wishlist

__author__ = 'Rico'


class DBwrapper(object):
    class __DBwrapper(object):
        dir_path = os.path.dirname(os.path.abspath(__file__))

        def __init__(self):
            database_path = os.path.join(self.dir_path, "users.db")

            if not os.path.exists(database_path):
                print("File '" + database_path + "' does not exist! Trying to create one.")
                try:
                    self.create_database(database_path)
                except:
                    print("An error has occurred while creating the database!")

            self.connection = sqlite3.connect(database_path)
            self.connection.text_factory = lambda x: str(x, 'utf-8', "ignore")
            self.cursor = self.connection.cursor()

        def create_database(self, database_path):
            # Create database file and add admin and users table to the database
            open(database_path, 'a').close()

            connection = sqlite3.connect(database_path)
            connection.text_factory = lambda x: str(x, 'utf-8', "ignore")
            cursor = connection.cursor()

            cursor.execute("CREATE TABLE 'users'"
                           "('user_id' INTEGER NOT NULL PRIMARY KEY UNIQUE,"
                           "'lang_id' TEXT NOT NULL DEFAULT 'en',"
                           "'first_name' TEXT);")

            cursor.execute("CREATE TABLE 'wishlists'"
                           "('wishlist_id' INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,"
                           "'name' TEXT NOT NULL DEFAULT 'Kein Titel',"
                           "'price' REAL NOT NULL DEFAULT 0,"
                           "'url' TEXT NOT NULL);")

            cursor.execute("CREATE TABLE 'UsersWishlists'"
                           "('wishlist_id' INTEGER NOT NULL UNIQUE,"
                           "'user_id' INTEGER NOT NULL,"
                           "FOREIGN KEY('wishlist_id') REFERENCES wishlists(wishlist_id),"
                           "FOREIGN KEY('user_id') REFERENCES users(user_id));")

            connection.commit()
            connection.close()

        def get_wishlists(self, user_id):
            self.cursor.execute("SELECT wishlists.wishlist_id, wishlists.url FROM wishlists "
                                "INNER JOIN UsersWishlists on UsersWishlists.wishlist_id=wishlists.wishlist_id "
                                "WHERE UsersWishlists.user_id=?;", [str(user_id)])
            return self.cursor.fetchall()

        def get_all_wishlists(self):
            self.cursor.execute("SELECT wishlist_id, name, price, url FROM wishlists;")
            wishlist_l = self.cursor.fetchall()
            wishlists = []

            for line in wishlist_l:
                wishlists.append(Wishlist(id=line[0], name=line[1], price=line[2], url=line[3]))

            return wishlists


        def get_wishlist_ids(self):
            self.cursor.execute("SELECT wishlists.wishlist_id FROM wishlists;")
            return self.cursor.fetchall()

        def subscribe_wishlist(self, id, user_id):
            self.cursor.execute("INSERT INTO UsersWishlists VALUES (?, ?);", [str(id), str(user_id)])
            self.connection.commit()

        def add_wishlist(self, id, name, price, url):
            self.cursor.execute("INSERT INTO wishlists (wishlist_id, name, price, url) VALUES (?, ?, ?, ?);", [str(id), str(name), str(price), str(url)])
            self.connection.commit()

        def unsubscribe_wishlist(self, user_id, wishlist_id):
            self.cursor.execute("DELETE FROM UsersWishlists WHERE user_id=? and wishlist_id=?;", [str(user_id), str(wishlist_id)])
            self.connection.commit()

        def get_user(self, user_id):
            self.cursor.execute("SELECT * FROM users WHERE user_id=?;", [str(user_id)])

            result = self.cursor.fetchone()
            if len(result) > 0:
                return result
            else:
                return []

        def get_users_from_wishlist(self, wishlist_id):
            self.cursor.execute("SELECT user_id FROM 'UsersWishlists' INNER JOIN Wishlists on Wishlists.wishlist_id=UsersWishlists.wishlist_id WHERE UsersWishlists.wishlist_id=?;", [str(wishlist_id)])
            user_list = self.cursor.fetchall()
            users = []

            for line in user_list:
                users.append(line[0])

            return users

        def get_wishlists_from_user(self, user_id):
            self.cursor.execute("SELECT wishlists.wishlist_id, wishlists.name, wishlists.price, wishlists.url FROM 'UsersWishlists' INNER JOIN Wishlists on Wishlists.wishlist_id=UsersWishlists.wishlist_id WHERE UsersWishlists.user_id=?;", [str(user_id)])
            wishlist_l = self.cursor.fetchall()
            wishlists = []

            for line in wishlist_l:
                wishlists.append(Wishlist(id=line[0], name=line[1], price=line[2], url=line[3]))

            return wishlists

        def get_all_users(self):
            self.cursor.execute("SELECT rowid, * FROM users;")
            return self.cursor.fetchall()

        def get_lang_id(self, user_id):
            self.cursor.execute("SELECT lang_id FROM users WHERE user_id=?;", [str(user_id)])
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                return "en"

        def add_user(self, user_id, lang_id, first_name):
            try:
                self.cursor.execute("INSERT INTO users VALUES (?, ?, ?);", (str(user_id), str(lang_id), str(first_name)))
                self.connection.commit()
            except sqlite3.IntegrityError:
                # print("User already exists")
                pass

        def is_user_saved(self, user_id):
            self.cursor.execute("SELECT rowid, * FROM users WHERE user_id=?;", [str(user_id)])

            result = self.cursor.fetchall()
            if len(result) > 0:
                return True
            else:
                return False

        def close_conn(self):
            self.connection.close()

    instance = None

    def __init__(self):
        if not DBwrapper.instance:
            DBwrapper.instance = DBwrapper.__DBwrapper()

    @staticmethod
    def get_instance():
        if not DBwrapper.instance:
            DBwrapper.instance = DBwrapper.__DBwrapper()

        return DBwrapper.instance
