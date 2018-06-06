# -*- coding: utf-8 -*-

import os
import unittest

from database.db_wrapper import DBwrapper


class DBWrapperTest(unittest.TestCase):

    def setUp(self):
        self.db_name = "test.db"
        self.db_name_test_create = "test_create.db"
        self.db = DBwrapper.get_instance(self.db_name)

    def tearDown(self):
        self.db.delete_all_tables()
        self.db.close_conn()
        try:
            test_db = os.path.join(self.db.dir_path, self.db_name)
            test_create_db = os.path.join(self.db.dir_path, self.db_name_test_create)
            os.remove(test_db)
            os.remove(test_create_db)
        except OSError as e:
            pass

        DBwrapper.instance = None

    def test_create_database(self):
        """Test for checking if the database gets created correctly"""
        # Use another path, since we want to check that method independendly from the initialization
        path = self.db.dir_path
        db_path = os.path.join(path, self.db_name_test_create)

        # Check if db file doesn't already exist
        self.assertFalse(os.path.exists(db_path))

        # Create database file
        self.db.create_database(db_path)

        # Check if the db file was created in the directory
        self.assertTrue(os.path.exists(db_path))

    def test_create_tables(self):
        """Test for checking if the database tables are created correctly"""
        table_names = ["users", "products", "wishlists", "product_prices", "wishlist_prices", "product_subscribers", "wishlist_subscribers"]

        # Use another path, since we want to check that method independendly from the initialization
        path = self.db.dir_path
        db_path = os.path.join(path, self.db_name_test_create)

        # Create database file
        self.db.create_database(db_path)
        self.db.setup_connection(db_path)

        # Make sure that tables are not already present in the database
        for table_name in table_names:
            result = self.db.cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?;", [table_name]).fetchone()[0]
            self.assertEqual(result, 0, msg="Table '{}' does already exist!".format(table_name))

        # Create tables in the database
        self.db.create_tables()

        # Make sure that all the tables are correctly created
        for table_name in table_names:
            result = self.db.cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?;", [table_name]).fetchone()[0]
            self.assertEqual(result, 1, msg="Table '{}' does not exist!".format(table_name))

    def test_add_wishlist(self):
        """Test for checking if wishlists are being added correctly"""
        wl_id = 123456
        wl_name = "Wishlist"
        wl_url = "https://geizhals.de/?cat=WL-123456"
        wl_price = 123.45

        # Make sure that element is not already in database
        result = self.db.cursor.execute("SELECT count(*) FROM wishlists WHERE wishlist_id=?", [wl_id]).fetchone()[0]
        self.assertEqual(result, 0)

        self.db.add_wishlist(id=wl_id, name=wl_name, url=wl_url, price=wl_price)
        result = self.db.cursor.execute("SELECT wishlist_id, name, url, price  FROM wishlists WHERE wishlist_id=?", [wl_id]).fetchone()

        self.assertEqual(result[0], wl_id, msg="ID is not equal!")
        self.assertEqual(result[1], wl_name, msg="Name is not equal!")
        self.assertEqual(result[2], wl_url, msg="Url is not equal!")
        self.assertEqual(result[3], wl_price, msg="Price is not equal!")

    def test_get_all_wishlists(self):
        """Test to check if all wishlists can be retreived from the db"""
        wishlists = [{"id": 962572, "name": "NIU2E0RRWX", "url": "https://geizhals.de/?cat=WL-962572", "price": 62.80},
                     {"id": 924729, "name": "3W5NQ1QIHT", "url": "https://geizhals.de/?cat=WL-924729", "price": 46.00},
                     {"id": 614044, "name": "CTYCTW798V", "url": "https://geizhals.de/?cat=WL-614044", "price": 96.95},
                     {"id": 245759, "name": "VDY66U0AWM", "url": "https://geizhals.de/?cat=WL-245759", "price": 53.94},
                     {"id": 490792, "name": "N6MCC1Z38O", "url": "https://geizhals.de/?cat=WL-490792", "price": 144.85},
                     {"id": 533484, "name": "NOJJ8KVE9T", "url": "https://geizhals.de/?cat=WL-533484", "price": 122.77},
                     {"id": 577007, "name": "ELV51DSL2A", "url": "https://geizhals.de/?cat=WL-577007", "price": 62.68},
                     {"id": 448441, "name": "6RM9F6IWIO", "url": "https://geizhals.de/?cat=WL-448441", "price": 45.97},
                     {"id": 567418, "name": "C2W75RPRFS", "url": "https://geizhals.de/?cat=WL-567418", "price": 137.53},
                     {"id": 590717, "name": "JEXP2E5Y06", "url": "https://geizhals.de/?cat=WL-590717", "price": 117.84}]

        for wl in wishlists:
            self.db.add_wishlist(id=wl.get("id"), name=wl.get("name"), url=wl.get("url"), price=wl.get("price"))

        db_wishlists = self.db.get_all_wishlists()

        for db_wl in db_wishlists:
            found = False
            for wl in wishlists:
                if db_wl.id == wl.get("id"):
                    found = True

            self.assertTrue(found, msg="Inserted wishlist was not found!")

    def test_get_all_products(self):
        products = [{"id": 962572, "name": "NIU2E0RRWX", "url": "https://geizhals.de/a962572", "price": 62.80},
                    {"id": 924729, "name": "3W5NQ1QIHT", "url": "https://geizhals.de/a924729", "price": 46.00},
                    {"id": 614044, "name": "CTYCTW798V", "url": "https://geizhals.de/a614044", "price": 96.95},
                    {"id": 245759, "name": "VDY66U0AWM", "url": "https://geizhals.de/a245759", "price": 53.94},
                    {"id": 490792, "name": "N6MCC1Z38O", "url": "https://geizhals.de/a490792", "price": 144.85},
                    {"id": 533484, "name": "NOJJ8KVE9T", "url": "https://geizhals.de/a533484", "price": 122.77},
                    {"id": 577007, "name": "ELV51DSL2A", "url": "https://geizhals.de/a577007", "price": 62.68},
                    {"id": 448441, "name": "6RM9F6IWIO", "url": "https://geizhals.de/a448441", "price": 45.97},
                    {"id": 567418, "name": "C2W75RPRFS", "url": "https://geizhals.de/a567418", "price": 137.53},
                    {"id": 590717, "name": "JEXP2E5Y06", "url": "https://geizhals.de/a590717", "price": 117.84}]
        for p in products:
            self.db.add_product(id=p.get("id"), name=p.get("name"), url=p.get("url"), price=p.get("price"))

        db_products = self.db.get_all_products()

        for db_p in db_products:
            found = False
            for p in products:
                if db_p.id == p.get("id"):
                    found = True

            self.assertTrue(found, msg="Inserted product was not found!")

    def test_add_wishlist(self):
        """Test for checking if wishlists are being added correctly"""
        wl_id = 123456
        wl_name = "Wishlist"
        wl_url = "https://geizhals.de/?cat=WL-123456"
        wl_price = 123.45

        # Make sure that element is not already in database
        result = self.db.cursor.execute("SELECT count(*) FROM wishlists WHERE wishlist_id=?", [wl_id]).fetchone()[0]
        self.assertEqual(result, 0)

        self.db.add_wishlist(id=wl_id, name=wl_name, url=wl_url, price=wl_price)
        result = self.db.cursor.execute("SELECT wishlist_id, name, url, price  FROM wishlists WHERE wishlist_id=?", [wl_id]).fetchone()

        self.assertEqual(result[0], wl_id, msg="ID is not equal!")
        self.assertEqual(result[1], wl_name, msg="Name is not equal!")
        self.assertEqual(result[2], wl_url, msg="Url is not equal!")
        self.assertEqual(result[3], wl_price, msg="Price is not equal!")

    def test_add_user(self):
        """Test to check if adding users works as expected"""
        user = {"id": 123456, "first_name": "John", "username": "testUsername", "lang_code": "en_US"}

        # Check that user does not already exist
        user_db = self.db.get_user(user.get("id"))
        self.assertEqual(user_db, None)

        # Add user to database
        self.db.add_user(user.get("id"), user.get("first_name"), user.get("username"), user.get("lang_code"))

        # Check if user was added
        user_db = self.db.get_user(user.get("id"))
        self.assertEqual(user_db.get("id"), user.get("id"))

    def test_is_user_saved(self):
        """Test to check if the 'check if a user exists' works as expected"""
        user = {"id": 123456, "first_name": "John", "username": "testUsername", "lang_code": "en_US"}

        # Check that user does not already exist
        user_db = self.db.get_user(user.get("id"))
        self.assertEqual(user_db, None)

        self.db.add_user(user.get("id"), user.get("first_name"), user.get("username"), user.get("lang_code"))

        self.assertTrue(self.db.is_user_saved(user.get("id")))
