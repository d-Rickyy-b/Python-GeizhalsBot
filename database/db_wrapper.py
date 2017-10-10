# -*- coding: utf-8 -*-
import os
import sqlite3

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
                           "('userID' INTEGER NOT NULL,"
                           "'languageID' TEXT,"
                           "'first_name' TEXT,"
                           "PRIMARY KEY('userID'));")
            connection.commit()
            connection.close()

        def get_user(self, user_id):
            self.cursor.execute("SELECT * FROM users WHERE user_id=?;", [str(user_id)])

            result = self.cursor.fetchone()
            if len(result) > 0:
                return result
            else:
                return []

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
