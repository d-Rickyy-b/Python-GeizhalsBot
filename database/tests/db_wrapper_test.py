# -*- coding: utf-8 -*-

import os
import unittest

from database.db_wrapper import DBwrapper
from geizhals.product import Product
from geizhals.wishlist import Wishlist


class DBWrapperTest(unittest.TestCase):

    def setUp(self):
        self.db_name = "test.db"
        self.db_name_test_create = "test_create.db"
        self.db = DBwrapper.get_instance(self.db_name)

        # Define sample wishlist and product
        self.wl = Wishlist(123456, "Wishlist", "https://geizhals.de/?cat=WL-123456", 123.45)
        self.p = Product(123456, "Product", "https://geizhals.de/a123456", 123.45)

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

    def test_get_subscribed_wishlist_count(self):
        user_id = 11223344
        first_name = "John"
        username = "JohnDoe"
        wl2 = Wishlist("9922113", "TestName", "https://geizhals.de/?cat=WL-123456", 12.12)

        self.db.add_wishlist(id=self.wl.id, name=self.wl.name, url=self.wl.url, price=self.wl.price)
        self.db.add_wishlist(id=wl2.id, name=wl2.name, url=wl2.url, price=wl2.price)

        # Make sure that count is 0 in the beginning
        self.db.add_user(user_id, first_name, username)
        count = self.db.get_subscribed_wishlist_count(user_id)
        self.assertEqual(count, 0)

        # Subscribe to first wishlist and check that count equals to 1
        self.db.subscribe_wishlist(self.wl.id, user_id)
        count = self.db.get_subscribed_wishlist_count(user_id)
        self.assertEqual(count, 1)

        # Subscribe to second wishlist and check that count equals to 2
        self.db.subscribe_wishlist(wl2.id, user_id)
        count = self.db.get_subscribed_wishlist_count(user_id)
        self.assertEqual(count, 2)

        # Check that after unsubscribing the count decreases
        self.db.unsubscribe_wishlist(user_id, self.wl.id)
        count = self.db.get_subscribed_wishlist_count(user_id)
        self.assertEqual(count, 1)

    def test_get_subscribed_product_count(self):
        user_id = 11223344
        first_name = "John"
        username = "JohnDoe"
        p2 = Product("9922113", "TestName", "https://geizhals.de/?cat=WL-123456", 12.12)

        self.db.add_product(id=self.p.id, name=self.p.name, url=self.p.url, price=self.p.price)
        self.db.add_product(id=p2.id, name=p2.name, url=p2.url, price=p2.price)

        # Make sure that count is 0 in the beginning
        self.db.add_user(user_id, first_name, username)
        count = self.db.get_subscribed_product_count(user_id)
        self.assertEqual(count, 0)

        # Subscribe to first product and check that count equals to 1
        self.db.subscribe_product(self.p.id, user_id)
        count = self.db.get_subscribed_product_count(user_id)
        self.assertEqual(count, 1)

        # Subscribe to second product and check that count equals to 2
        self.db.subscribe_product(p2.id, user_id)
        count = self.db.get_subscribed_product_count(user_id)
        self.assertEqual(count, 2)

        # Check that after unsubscribing the count decreases
        self.db.unsubscribe_product(user_id, self.p.id)
        count = self.db.get_subscribed_product_count(user_id)
        self.assertEqual(count, 1)

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

        for wl in wishlists:
            found = False
            for db_wl in db_wishlists:
                if db_wl.id == wl.get("id"):
                    found = True

            self.assertTrue(found, msg="Inserted wishlist {} was not found!".format(wl.get("id")))

    def test_get_all_products(self):
        """Test to check if retreiving all products works"""
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

    def test_get_wishlist_info(self):
        """Test to check if fetching information for a wishlist works"""
        self.assertFalse(self.db.is_wishlist_saved(self.wl.id), "Wishlist is already saved!")

        self.db.add_wishlist(self.wl.id, self.wl.name, self.wl.price, self.wl.url)
        wishlist = self.db.get_wishlist_info(self.wl.id)

        self.assertEqual(wishlist.id, self.wl.id)
        self.assertEqual(wishlist.name, self.wl.name)
        self.assertEqual(wishlist.url, self.wl.url)
        self.assertEqual(wishlist.price, self.wl.price)

    def test_is_wishlist_saved(self):
        # Check if wishlist is already saved
        self.assertFalse(self.db.is_wishlist_saved(self.wl.id), "Wishlist is already saved!")

        # Add wishlist to the database
        self.db.add_wishlist(self.wl.id, self.wl.name, self.wl.price, self.wl.url)

        # Check if wishlist is now saved in the db
        self.assertTrue(self.db.is_wishlist_saved(self.wl.id), "Wishlist is not saved in the db!")

    def test_is_product_saved(self):
        # Make sure product is not already saved
        self.assertFalse(self.db.is_product_saved(self.p.id), "Product should not be saved yet!")

        # Add product to the db
        self.db.add_product(self.p.id, self.p.name, self.p.price, self.p.url)

        # Check if product is saved afterwards
        self.assertTrue(self.db.is_product_saved(self.p.id), "Product is not saved in the db!")

    def test_add_wishlist(self):
        """Test for checking if wishlists are being added correctly"""
        # Make sure that element is not already in database
        result = self.db.cursor.execute("SELECT count(*) FROM wishlists WHERE wishlist_id=?", [self.wl.id]).fetchone()[0]
        self.assertEqual(result, 0)

        self.db.add_wishlist(id=self.wl.id, name=self.wl.name, url=self.wl.url, price=self.wl.price)
        result = self.db.cursor.execute("SELECT wishlist_id, name, url, price  FROM wishlists WHERE wishlist_id=?", [self.wl.id]).fetchone()

        self.assertEqual(result[0], self.wl.id, msg="ID is not equal!")
        self.assertEqual(result[1], self.wl.name, msg="Name is not equal!")
        self.assertEqual(result[2], self.wl.url, msg="Url is not equal!")
        self.assertEqual(result[3], self.wl.price, msg="Price is not equal!")

    def test_add_product(self):
        """Test for checking if products are being added correctly"""
        # Make sure that element is not already in database
        result = self.db.cursor.execute("SELECT count(*) FROM products WHERE product_id=?", [self.p.id]).fetchone()[0]
        self.assertEqual(result, 0)

        # Check if product is saved afterwards
        self.db.add_product(id=self.p.id, name=self.p.name, url=self.p.url, price=self.p.price)
        result = self.db.cursor.execute("SELECT product_id, name, url, price FROM products WHERE product_id=?", [self.p.id]).fetchone()

        self.assertEqual(result[0], self.p.id, msg="ID is not equal!")
        self.assertEqual(result[1], self.p.name, msg="Name is not equal!")
        self.assertEqual(result[2], self.p.url, msg="Url is not equal!")
        self.assertEqual(result[3], self.p.price, msg="Price is not equal!")

    def test_rm_wishlist(self):
        """Test for checking if removing a wishlist works as intended"""
        # Add wishlist and check if it's in the db
        self.assertFalse(self.db.is_wishlist_saved(self.wl.id))
        self.db.add_wishlist(self.wl.id, self.wl.name, self.wl.price, self.wl.url)
        self.assertTrue(self.db.is_wishlist_saved(self.wl.id))

        # Check if wishlist gets removed properly
        self.db.rm_wishlist(self.wl.id)
        self.assertFalse(self.db.is_wishlist_saved(self.wl.id))

    def test_rm_product(self):
        """Test for checking if removing a product works as intended"""
        # Add product and check if it's in the db
        self.assertFalse(self.db.is_product_saved(self.p.id))
        self.db.add_product(self.p.id, self.p.name, self.p.price, self.p.url)
        self.assertTrue(self.db.is_product_saved(self.p.id))

        # Check if product gets removed properly
        self.db.rm_product(self.p.id)
        self.assertFalse(self.db.is_product_saved(self.p.id))

    def test_subscribe_wishlist(self):
        """Test for checking if subscribing a wishlist works as intended"""
        user_id = 11223344
        first_name = "John"
        username = "JohnDoe"

        self.db.add_wishlist(id=self.wl.id, name=self.wl.name, url=self.wl.url, price=self.wl.price)
        self.db.add_user(user_id, first_name, username)

        result = self.db.cursor.execute("SELECT wishlist_id FROM wishlist_subscribers AS ws WHERE ws.user_id=? AND ws.wishlist_id=?;", [str(user_id), str(self.wl.id)]).fetchone()
        self.assertEqual(result, None)

        self.db.subscribe_wishlist(self.wl.id, user_id)
        result = self.db.cursor.execute("SELECT wishlist_id FROM wishlist_subscribers AS ws WHERE ws.user_id=? AND ws.wishlist_id=?;", [str(user_id), str(self.wl.id)]).fetchone()

        self.assertEqual(len(result), 1)

    def test_subscribe_product(self):
        """Test for checking if subscribing a product works as intended"""
        user_id = 11223344
        first_name = "John"
        username = "JohnDoe"

        self.db.add_product(id=self.p.id, name=self.p.name, url=self.p.url, price=self.p.price)
        self.db.add_user(user_id, first_name, username)

        result = self.db.cursor.execute("SELECT product_id FROM product_subscribers AS ps WHERE ps.user_id=? AND ps.product_id=?;", [str(user_id), str(self.p.id)]).fetchone()
        self.assertIsNone(result)

        self.db.subscribe_product(self.p.id, user_id)
        result = self.db.cursor.execute("SELECT product_id FROM product_subscribers AS ps WHERE ps.user_id=? AND ps.product_id=?;", [str(user_id), str(self.p.id)]).fetchone()

        self.assertEqual(len(result), 1)

    def test_unsubscribe_wishlist(self):
        """Test for checking if unsubscribing a wishlist works as intended"""
        user_id = 11223344
        first_name = "John"
        username = "JohnDoe"

        self.db.add_wishlist(id=self.wl.id, name=self.wl.name, url=self.wl.url, price=self.wl.price)
        self.db.add_user(user_id, first_name, username)
        self.db.subscribe_wishlist(self.wl.id, user_id)

        result = self.db.cursor.execute("SELECT wishlist_id FROM wishlist_subscribers AS ws WHERE ws.user_id=? AND ws.wishlist_id=?;", [str(user_id), str(self.wl.id)]).fetchone()
        self.assertEqual(len(result), 1)

        self.db.unsubscribe_wishlist(user_id, self.wl.id)
        result = self.db.cursor.execute("SELECT wishlist_id FROM wishlist_subscribers AS ws WHERE ws.user_id=? AND ws.wishlist_id=?;", [str(user_id), str(self.wl.id)]).fetchone()

        self.assertIsNone(result)

    def test_unsubscribe_product(self):
        """Test for checking if unsubscribing a product works as intended"""
        user_id = 11223344
        first_name = "John"
        username = "JohnDoe"

        self.db.add_product(id=self.p.id, name=self.p.name, url=self.p.url, price=self.p.price)
        self.db.add_user(user_id, first_name, username)
        self.db.subscribe_product(self.p.id, user_id)
        result = self.db.cursor.execute("SELECT product_id FROM product_subscribers AS ps WHERE ps.user_id=? AND ps.product_id=?;", [str(user_id), str(self.p.id)]).fetchone()
        self.assertEqual(len(result), 1)

        self.db.unsubscribe_product(user_id, self.p.id)
        result = self.db.cursor.execute("SELECT product_id FROM product_subscribers AS ps WHERE ps.user_id=? AND ps.product_id=?;", [str(user_id), str(self.p.id)]).fetchone()

        self.assertIsNone(result)

    def test_get_user(self):
        """Test to check if getting user information works as intended"""
        # Check that None is returned if no user is saved
        user = {"id": 415641, "first_name": "Peter", "username": "name2", "lang_code": "en_US"}

        user_db = self.db.get_user(user.get("id"))
        self.assertIsNone(user_db)

        self.db.add_user(user.get("id"), user.get("first_name"), user.get("username"), user.get("lang_code"))
        user_db = self.db.get_user(user.get("id"))

        self.assertEqual(user_db.id, user.get("id"))
        self.assertEqual(user_db.first_name, user.get("first_name"))
        self.assertEqual(user_db.username, user.get("username"))
        self.assertEqual(user_db.lang_code, user.get("lang_code"))

    def test_get_wishlists_for_user(self):
        """Test to check if getting wishlists for a user works as intended"""
        user = {"id": 415641, "first_name": "Peter", "username": "jkopsdfjk", "lang_code": "en_US"}

        wl1 = Wishlist(123123, "Wishlist", "https://geizhals.de/?cat=WL-123123", 123.45)
        wl2 = Wishlist(987123, "Wishlist2", "https://geizhals.de/?cat=WL-987123", 1.23)
        wl3 = Wishlist(4567418, "Wishlist3", "https://geizhals.de/?cat=WL-987123", 154.00)
        local_wishlists = [wl1, wl2]

        # Add user
        self.db.add_user(user.get("id"), user.get("first_name"), user.get("username"), user.get("lang_code"))

        # Add wishlist1 & wishlist2 & wishlist3
        self.db.add_wishlist(wl1.id, wl1.name, wl1.price, wl1.url)
        self.db.add_wishlist(wl2.id, wl2.name, wl2.price, wl2.url)
        self.db.add_wishlist(wl3.id, wl3.name, wl3.price, wl3.url)

        # Subscribe user to wishlist1 & wishlist2
        self.db.subscribe_wishlist(wl1.id, user.get("id"))
        self.db.subscribe_wishlist(wl2.id, user.get("id"))

        # Check if wishlists are in the return value
        wishlists = self.db.get_wishlists_for_user(user.get("id"))

        # Make sure that both lists are the same length
        self.assertEqual(len(wishlists), len(local_wishlists))

        for local_wishlist in local_wishlists:
            found = False
            for wishlist in wishlists:
                if wishlist.id == local_wishlist.id:
                    found = True
                    break

            # Make sure that each subscribed wishlist is in the list
            self.assertTrue(found)

    def test_get_products_for_user(self):
        """Test to check if getting products for a user works as intended"""
        user = {"id": 415641, "first_name": "Peter", "username": "jkopsdfjk", "lang_code": "en_US"}

        p1 = Product(123123, "Product", "https://geizhals.de/?cat=WL-123123", 123.45)
        p2 = Product(987123, "Product2", "https://geizhals.de/?cat=WL-987123", 1.23)
        p3 = Product(4567418, "Product3", "https://geizhals.de/?cat=WL-987123", 154.00)
        local_products = [p1, p2]

        # Add user
        self.db.add_user(user.get("id"), user.get("first_name"), user.get("username"), user.get("lang_code"))
        
        # Add product1 & product2 & product3
        self.db.add_product(p1.id, p1.name, p1.price, p1.url)
        self.db.add_product(p2.id, p2.name, p2.price, p2.url)
        self.db.add_product(p3.id, p3.name, p3.price, p3.url)

        # Subscribe user to product1 & product2
        self.db.subscribe_product(p1.id, user.get("id"))
        self.db.subscribe_product(p2.id, user.get("id"))

        # Check if products are in the return value
        products = self.db.get_products_for_user(user.get("id"))

        # Make sure that both lists are the same length
        self.assertEqual(len(products), len(local_products))

        for local_product in local_products:
            found = False
            for product in products:
                if product.id == local_product.id:
                    found = True
                    break

            # Make sure that each subscribed product is in the list
            self.assertTrue(found)

    def test_is_user_wishlist_subscriber(self):
        user1 = {"id": 415641, "first_name": "Peter", "username": "jkopsdfjk", "lang_code": "en_US"}
        user2 = {"id": 123456, "first_name": "John", "username": "ölyjsdf", "lang_code": "de"}

        wl1 = Wishlist(123123, "Wishlist", "https://geizhals.de/?cat=WL-123123", 123.45)
        wl2 = Wishlist(987123, "Wishlist2", "https://geizhals.de/?cat=WL-987123", 1.23)

        # Add user1, add user2
        self.db.add_user(user1.get("id"), user1.get("first_name"), user1.get("username"), user1.get("lang_code"))
        self.db.add_user(user2.get("id"), user2.get("first_name"), user2.get("username"), user2.get("lang_code"))
        # Add wishlist1, add wishlist2
        self.db.add_wishlist(wl1.id, wl1.name, wl1.price, wl1.url)
        self.db.add_wishlist(wl2.id, wl2.name, wl2.price, wl2.url)

        # subscribe user1 to wishlist1
        self.db.subscribe_wishlist(wl1.id, user1.get("id"))

        # subscribe user2 to wishlist2
        self.db.subscribe_wishlist(wl2.id, user2.get("id"))

        # check if user1 is subscribed to wishlist1 -> True
        self.assertTrue(self.db.is_user_wishlist_subscriber(user1.get("id"), wl1.id))

        # check if user2 is subscribed to wishlist1 -> False
        self.assertFalse(self.db.is_user_wishlist_subscriber(user2.get("id"), wl1.id))

        # check if user1 is subscribed to wishlist2 -> False
        self.assertFalse(self.db.is_user_wishlist_subscriber(user1.get("id"), wl2.id))

        # check if user2 is subscribed to wishlist2 -> True
        self.assertTrue(self.db.is_user_wishlist_subscriber(user2.get("id"), wl2.id))

    def test_is_user_product_subscriber(self):
        """Check if """
        user1 = {"id": 415641, "first_name": "Peter", "username": "jkopsdfjk", "lang_code": "en_US"}
        user2 = {"id": 123456, "first_name": "John", "username": "ölyjsdf", "lang_code": "de"}

        p1 = Product(123123, "Product", "https://geizhals.de/?cat=WL-123123", 123.45)
        p2 = Product(987123, "Product2", "https://geizhals.de/?cat=WL-987123", 1.23)

        # Add user1, add user2
        self.db.add_user(user1.get("id"), user1.get("first_name"), user1.get("username"), user1.get("lang_code"))
        self.db.add_user(user2.get("id"), user2.get("first_name"), user2.get("username"), user2.get("lang_code"))
        # Add product1, add product2
        self.db.add_product(p1.id, p1.name, p1.price, p1.url)
        self.db.add_product(p2.id, p2.name, p2.price, p2.url)

        # subscribe user1 to product1
        self.db.subscribe_product(p1.id, user1.get("id"))

        # subscribe user2 to product2
        self.db.subscribe_product(p2.id, user2.get("id"))

        # check if user1 is subscribed to product1 -> True
        self.assertTrue(self.db.is_user_product_subscriber(user1.get("id"), p1.id))

        # check if user2 is subscribed to product1 -> False
        self.assertFalse(self.db.is_user_product_subscriber(user2.get("id"), p1.id))

        # check if user1 is subscribed to product2 -> False
        self.assertFalse(self.db.is_user_product_subscriber(user1.get("id"), p2.id))

        # check if user2 is subscribed to product2 -> True
        self.assertTrue(self.db.is_user_product_subscriber(user2.get("id"), p2.id))

    def test_update_wishlist_name(self):
        self.db.add_wishlist(self.wl.id, self.wl.name, self.wl.price, self.wl.url)
        self.assertEqual(self.db.get_wishlist_info(self.wl.id).name, self.wl.name)

        self.db.update_wishlist_name(self.wl.id, "New Wishlist")
        self.assertEqual(self.db.get_wishlist_info(self.wl.id).name, "New Wishlist")

    def test_update_product_name(self):
        self.db.add_product(self.p.id, self.p.name, self.p.price, self.p.url)
        self.assertEqual(self.db.get_product_info(self.p.id).name, self.p.name)

        self.db.update_product_name(self.p.id, "New Product")
        self.assertEqual(self.db.get_product_info(self.p.id).name, "New Product")

    def test_update_wishlist_price(self):
        """Test to check if updating the wishlist price in the database works as intended"""
        new_price = 999.99
        self.db.add_wishlist(self.wl.id, self.wl.name, self.wl.price, self.wl.url)
        self.db.update_wishlist_price(wishlist_id=self.wl.id, price=new_price)

        price = self.db.cursor.execute("SELECT price FROM wishlists WHERE wishlist_id=?", [self.wl.id]).fetchone()[0]

        self.assertEqual(price, new_price)

    def test_update_product_price(self):
        """Test to check if updating the product price in the database works as intended"""
        new_price = 999.99
        self.db.add_product(self.p.id, self.p.name, self.p.price, self.p.url)
        self.db.update_product_price(product_id=self.p.id, price=new_price)

        price = self.db.cursor.execute("SELECT price FROM products WHERE product_id=?", [self.p.id]).fetchone()[0]

        self.assertEqual(price, new_price)

    def test_get_all_users(self):
        """Test to check if retreiving all users from the database works"""
        users = [{"id": 415641, "first_name": "Peter", "username": "name2", "lang_code": "en_US"},
                 {"id": 564864654, "first_name": "asdf", "username": "AnotherUser", "lang_code": "en_US"},
                 {"id": 54564162, "first_name": "NoName", "username": "Metallica", "lang_code": "en_US"},
                 {"id": 5555333, "first_name": "1234", "username": "d_Rickyy_b", "lang_code": "en_US"}]

        # Check that database is empty
        all_users_db = self.db.get_all_users()
        self.assertEqual(len(all_users_db), 0, msg="There are already users in the db!")

        for user in users:
            self.db.add_user(user.get("id"), user.get("first_name"), user.get("username"), user.get("lang_code"))

        all_users_db = self.db.get_all_users()

        self.assertEqual(len(all_users_db), len(users), msg="Users in database is not same amount as users in test!")

        for db_user in all_users_db:
            found = False

            for user in users:
                if user.get("id") == db_user.get("id"):
                    found = True
                    self.assertEqual(user.get("first_name"), db_user.get("first_name"))
                    self.assertEqual(user.get("username"), db_user.get("username"))
                    self.assertEqual(user.get("lang_code"), db_user.get("lang_code"))
                    break

            self.assertTrue(found)

    def test_get_lang_id(self):
        """Test to check if receiving the lang_code works"""
        user = {"id": 123456, "first_name": "John", "username": "testUsername", "lang_code": "en_US"}

        # Check that user does not already exist
        user_db = self.db.get_user(user.get("id"))
        self.assertEqual(user_db, None)

        # Add user to database
        self.db.add_user(user.get("id"), user.get("first_name"), user.get("username"), user.get("lang_code"))

        lang_id = self.db.get_lang_id(user.get("id"))
        self.assertEqual(lang_id, user.get("lang_code"))

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
        self.assertEqual(user_db.id, user.get("id"))

    def test_is_user_saved(self):
        """Test to check if the 'check if a user exists' works as expected"""
        user = {"id": 123456, "first_name": "John", "username": "testUsername", "lang_code": "en_US"}

        # Check that user does not already exist
        user_db = self.db.get_user(user.get("id"))
        self.assertIsNone(user_db, "User is not None!")
        self.assertFalse(self.db.is_user_saved(user.get("id")))

        self.db.add_user(user.get("id"), user.get("first_name"), user.get("username"), user.get("lang_code"))

        self.assertTrue(self.db.is_user_saved(user.get("id")))
