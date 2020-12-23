# -*- coding: utf-8 -*-

import unittest

from database.db_wrapper import Database
from geizhals.entities import Product, Wishlist


class DBWrapperTest(unittest.TestCase):

    def setUp(self):
        self.db_name = "test.db"
        self.db_name_test_create = "test_create.db"
        self.db = Database(self.db_name)

        # Define sample wishlist and product
        self.wl = Wishlist(123456, "Wishlist", "https://geizhals.de/?cat=WL-123456", 123.45)
        self.p = Product(123456, "Product", "https://geizhals.de/a123456", 123.45)
        self.user = {"user_id": 415641, "first_name": "Peter", "last_name": "Müller", "username": "jkopsdfjk", "lang_code": "en_US"}
        self.user2 = {"user_id": 123456, "first_name": "John", "last_name": "Doe", "username": "ölyjsdf", "lang_code": "de"}

    def tearDown(self):
        self.db.delete_all_tables()
        self.db.close_conn()

        try:
            test_db = self.db.dir_path / self.db_name
            test_db.unlink()
        except OSError as e:
            print(e)

        try:
            test_create_db = self.db.dir_path / self.db_name_test_create
            test_create_db.unlink()
        except Exception as e:
            print(e)

        Database._instance = None

    def helper_add_user(self, user):
        self.db.add_user(user.get("user_id"), user.get("first_name"), user.get("last_name"), user.get("username"), user.get("lang_code"))

    def test_create_database(self):
        """Test for checking if the database gets created correctly"""
        # Use another path, since we want to check that method independendly from the initialization
        db_path = self.db.dir_path / self.db_name_test_create

        # Check if db file doesn't already exist
        self.assertFalse(db_path.exists())

        # Create database file
        self.db.create_database(db_path)

        # Check if the db file was created in the directory
        self.assertTrue(db_path.exists())

    def test_create_tables(self):
        """Test for checking if the database tables are created correctly"""
        table_names = ["users", "products", "wishlists", "product_prices", "wishlist_prices", "product_subscribers", "wishlist_subscribers"]

        # Use another path, since we want to check that method independendly from the initialization
        db_path = self.db.dir_path / self.db_name_test_create

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
        """Test to check if the subscribed wishlist count is correct"""
        user_id = 11223344
        first_name = "John"
        last_name = "Doe"
        username = "JohnDoe"
        wl2 = Wishlist("9922113", "TestName", "https://geizhals.de/?cat=WL-123456", 12.12)

        self.db.add_wishlist(wishlist_id=self.wl.entity_id, name=self.wl.name, url=self.wl.url, price=self.wl.price)
        self.db.add_wishlist(wishlist_id=wl2.entity_id, name=wl2.name, url=wl2.url, price=wl2.price)

        # Make sure that count is 0 in the beginning
        self.db.add_user(user_id, first_name, last_name, username)
        count = self.db.get_subscribed_wishlist_count(user_id)
        self.assertEqual(count, 0)

        # Subscribe to first wishlist and check that count equals to 1
        self.db.subscribe_wishlist(self.wl.entity_id, user_id)
        count = self.db.get_subscribed_wishlist_count(user_id)
        self.assertEqual(count, 1)

        # Subscribe to second wishlist and check that count equals to 2
        self.db.subscribe_wishlist(wl2.entity_id, user_id)
        count = self.db.get_subscribed_wishlist_count(user_id)
        self.assertEqual(count, 2)

        # Check that after unsubscribing the count decreases
        self.db.unsubscribe_wishlist(user_id, self.wl.entity_id)
        count = self.db.get_subscribed_wishlist_count(user_id)
        self.assertEqual(count, 1)

    def test_get_subscribed_product_count(self):
        """Test to check if the subscribed product count is correct"""
        user_id = 11223344
        first_name = "John"
        last_name = "Doe"
        username = "JohnDoe"
        p2 = Product("9922113", "TestName", "https://geizhals.de/?cat=WL-123456", 12.12)

        self.db.add_product(product_id=self.p.entity_id, name=self.p.name, url=self.p.url, price=self.p.price)
        self.db.add_product(product_id=p2.entity_id, name=p2.name, url=p2.url, price=p2.price)

        # Make sure that count is 0 in the beginning
        self.db.add_user(user_id, first_name, last_name, username)
        count = self.db.get_subscribed_product_count(user_id)
        self.assertEqual(count, 0)

        # Subscribe to first product and check that count equals to 1
        self.db.subscribe_product(self.p.entity_id, user_id)
        count = self.db.get_subscribed_product_count(user_id)
        self.assertEqual(count, 1)

        # Subscribe to second product and check that count equals to 2
        self.db.subscribe_product(p2.entity_id, user_id)
        count = self.db.get_subscribed_product_count(user_id)
        self.assertEqual(count, 2)

        # Check that after unsubscribing the count decreases
        self.db.unsubscribe_product(user_id, self.p.entity_id)
        count = self.db.get_subscribed_product_count(user_id)
        self.assertEqual(count, 1)

    def test_get_all_wishlists(self):
        """Test to check if all wishlists can be retreived from the db"""
        wishlists = [{"entity_id": 962572, "name": "NIU2E0RRWX", "url": "https://geizhals.de/?cat=WL-962572", "price": 62.80},
                     {"entity_id": 924729, "name": "3W5NQ1QIHT", "url": "https://geizhals.de/?cat=WL-924729", "price": 46.00},
                     {"entity_id": 614044, "name": "CTYCTW798V", "url": "https://geizhals.de/?cat=WL-614044", "price": 96.95},
                     {"entity_id": 245759, "name": "VDY66U0AWM", "url": "https://geizhals.de/?cat=WL-245759", "price": 53.94},
                     {"entity_id": 490792, "name": "N6MCC1Z38O", "url": "https://geizhals.de/?cat=WL-490792", "price": 144.85},
                     {"entity_id": 533484, "name": "NOJJ8KVE9T", "url": "https://geizhals.de/?cat=WL-533484", "price": 122.77},
                     {"entity_id": 577007, "name": "ELV51DSL2A", "url": "https://geizhals.de/?cat=WL-577007", "price": 62.68},
                     {"entity_id": 448441, "name": "6RM9F6IWIO", "url": "https://geizhals.de/?cat=WL-448441", "price": 45.97},
                     {"entity_id": 567418, "name": "C2W75RPRFS", "url": "https://geizhals.de/?cat=WL-567418", "price": 137.53},
                     {"entity_id": 590717, "name": "JEXP2E5Y06", "url": "https://geizhals.de/?cat=WL-590717", "price": 117.84}]

        for wl in wishlists:
            self.db.add_wishlist(wishlist_id=wl.get("entity_id"), name=wl.get("name"), url=wl.get("url"), price=wl.get("price"))

        db_wishlists = self.db.get_all_wishlists()

        for wl in wishlists:
            for db_wl in db_wishlists:
                if db_wl.entity_id == wl.get("entity_id"):
                    break
            else:
                self.fail(msg="Inserted wishlist {} was not found!".format(wl.get("entity_id")))

    def test_get_all_subscribed_wishlists(self):
        """Test to check if retrieving subscribed wishlists works"""
        wishlists = [{"entity_id": 962572, "name": "NIU2E0RRWX", "url": "https://geizhals.de/?cat=WL-962572", "price": 62.80},
                     {"entity_id": 924729, "name": "3W5NQ1QIHT", "url": "https://geizhals.de/?cat=WL-924729", "price": 46.00},
                     {"entity_id": 614044, "name": "CTYCTW798V", "url": "https://geizhals.de/?cat=WL-614044", "price": 96.95},
                     {"entity_id": 245759, "name": "VDY66U0AWM", "url": "https://geizhals.de/?cat=WL-245759", "price": 53.94},
                     {"entity_id": 490792, "name": "N6MCC1Z38O", "url": "https://geizhals.de/?cat=WL-490792", "price": 144.85},
                     {"entity_id": 533484, "name": "NOJJ8KVE9T", "url": "https://geizhals.de/?cat=WL-533484", "price": 122.77},
                     {"entity_id": 577007, "name": "ELV51DSL2A", "url": "https://geizhals.de/?cat=WL-577007", "price": 62.68},
                     {"entity_id": 448441, "name": "6RM9F6IWIO", "url": "https://geizhals.de/?cat=WL-448441", "price": 45.97},
                     {"entity_id": 567418, "name": "C2W75RPRFS", "url": "https://geizhals.de/?cat=WL-567418", "price": 137.53},
                     {"entity_id": 590717, "name": "JEXP2E5Y06", "url": "https://geizhals.de/?cat=WL-590717", "price": 117.84}]

        for wl in wishlists:
            self.db.add_wishlist(wishlist_id=wl.get("entity_id"), name=wl.get("name"), url=wl.get("url"), price=wl.get("price"))

        # Add two users - otherwise we cannot subscribe
        self.db.add_user(1234, "Test user 1", "Doe", "Testie")
        self.db.add_user(1337, "Test user 2", "Doe", "Tester")

        # No subscriptions to start with
        self.assertEqual(0, len(self.db.get_all_subscribed_wishlists()), "There are already subscriptions!")

        # Subscribe by the first user - must be 1
        self.db.subscribe_wishlist(924729, 1234)
        self.assertEqual(1, len(self.db.get_all_subscribed_wishlists()), "Subscribed user is not counted!")

        # Subscribe by another user and check if it's still 1
        self.db.subscribe_wishlist(924729, 1337)
        self.assertEqual(1, len(self.db.get_all_subscribed_wishlists()), "Wishlist with two subscribers is counted twice!")

        # Subscribe another product by a user and check if it's 2
        self.db.subscribe_wishlist(245759, 1337)
        self.assertEqual(2, len(self.db.get_all_subscribed_wishlists()), "Two subscribed wishlists are not counted correctly")

    def test_get_all_products(self):
        """Test to check if retreiving all products works"""
        products = [{"entity_id": 962572, "name": "NIU2E0RRWX", "url": "https://geizhals.de/a962572", "price": 62.80},
                    {"entity_id": 924729, "name": "3W5NQ1QIHT", "url": "https://geizhals.de/a924729", "price": 46.00},
                    {"entity_id": 614044, "name": "CTYCTW798V", "url": "https://geizhals.de/a614044", "price": 96.95},
                    {"entity_id": 245759, "name": "VDY66U0AWM", "url": "https://geizhals.de/a245759", "price": 53.94},
                    {"entity_id": 490792, "name": "N6MCC1Z38O", "url": "https://geizhals.de/a490792", "price": 144.85},
                    {"entity_id": 533484, "name": "NOJJ8KVE9T", "url": "https://geizhals.de/a533484", "price": 122.77},
                    {"entity_id": 577007, "name": "ELV51DSL2A", "url": "https://geizhals.de/a577007", "price": 62.68},
                    {"entity_id": 448441, "name": "6RM9F6IWIO", "url": "https://geizhals.de/a448441", "price": 45.97},
                    {"entity_id": 567418, "name": "C2W75RPRFS", "url": "https://geizhals.de/a567418", "price": 137.53},
                    {"entity_id": 590717, "name": "JEXP2E5Y06", "url": "https://geizhals.de/a590717", "price": 117.84}]
        for p in products:
            self.db.add_product(product_id=p.get("entity_id"), name=p.get("name"), url=p.get("url"), price=p.get("price"))

        db_products = self.db.get_all_products()

        for db_p in db_products:
            for p in products:
                if db_p.entity_id == p.get("entity_id"):
                    break
            else:
                self.fail(msg="Inserted product was not found!")

    def test_get_all_subscribed_products(self):
        """Test to check if retrieving subscribed products works"""
        products = [{"entity_id": 962572, "name": "NIU2E0RRWX", "url": "https://geizhals.de/a962572", "price": 62.80},
                    {"entity_id": 924729, "name": "3W5NQ1QIHT", "url": "https://geizhals.de/a924729", "price": 46.00},
                    {"entity_id": 614044, "name": "CTYCTW798V", "url": "https://geizhals.de/a614044", "price": 96.95},
                    {"entity_id": 245759, "name": "VDY66U0AWM", "url": "https://geizhals.de/a245759", "price": 53.94},
                    {"entity_id": 490792, "name": "N6MCC1Z38O", "url": "https://geizhals.de/a490792", "price": 144.85},
                    {"entity_id": 533484, "name": "NOJJ8KVE9T", "url": "https://geizhals.de/a533484", "price": 122.77},
                    {"entity_id": 577007, "name": "ELV51DSL2A", "url": "https://geizhals.de/a577007", "price": 62.68},
                    {"entity_id": 448441, "name": "6RM9F6IWIO", "url": "https://geizhals.de/a448441", "price": 45.97},
                    {"entity_id": 567418, "name": "C2W75RPRFS", "url": "https://geizhals.de/a567418", "price": 137.53},
                    {"entity_id": 590717, "name": "JEXP2E5Y06", "url": "https://geizhals.de/a590717", "price": 117.84}]
        for p in products:
            self.db.add_product(product_id=p.get("entity_id"), name=p.get("name"), url=p.get("url"), price=p.get("price"))

        # Add two users - otherwise we cannot subscribe
        self.db.add_user(1234, "Test user 1", "Doe", "Testie")
        self.db.add_user(1337, "Test user 2", "Doe", "Tester")

        # No subscriptions to start with
        self.assertEqual(0, len(self.db.get_all_subscribed_products()), "There are already subscriptions!")

        # Subscribe by the first user - must be 1
        self.db.subscribe_product(924729, 1234)
        self.assertEqual(1, len(self.db.get_all_subscribed_products()), "Subscribed user is not counted!")

        # Subscribe by another user and check if it's still 1
        self.db.subscribe_product(924729, 1337)
        self.assertEqual(1, len(self.db.get_all_subscribed_products()), "Product with two subscribers is counted twice!")

        # Subscribe another product by a user and check if it's 2
        self.db.subscribe_product(245759, 1337)
        self.assertEqual(2, len(self.db.get_all_subscribed_products()), "Two subscribed products are not counted correctly")

    def test_get_wishlist_info(self):
        """Test to check if fetching information for a wishlist works"""
        self.assertFalse(self.db.is_wishlist_saved(self.wl.entity_id), "Wishlist is already saved!")

        self.db.add_wishlist(self.wl.entity_id, self.wl.name, self.wl.price, self.wl.url)
        wishlist = self.db.get_wishlist_info(self.wl.entity_id)

        self.assertEqual(wishlist.entity_id, self.wl.entity_id)
        self.assertEqual(wishlist.name, self.wl.name)
        self.assertEqual(wishlist.url, self.wl.url)
        self.assertEqual(wishlist.price, self.wl.price)

        self.assertIsNone(self.db.get_wishlist_info("23123123"))

    def test_get_product_info(self):
        """Test to check if fetching information for a product works"""
        self.assertFalse(self.db.is_product_saved(self.p.entity_id), "Product is already saved!")

        self.db.add_product(self.p.entity_id, self.p.name, self.p.price, self.p.url)
        product = self.db.get_product_info(self.p.entity_id)

        self.assertEqual(product.entity_id, self.p.entity_id)
        self.assertEqual(product.name, self.p.name)
        self.assertEqual(product.url, self.p.url)
        self.assertEqual(product.price, self.p.price)

        self.assertIsNone(self.db.get_product_info("23123123"))

    def test_is_wishlist_saved(self):
        """Test to check if is_wishlist_saved method works as intended"""
        # Check if wishlist is already saved
        self.assertFalse(self.db.is_wishlist_saved(self.wl.entity_id), "Wishlist is already saved!")

        # Add wishlist to the database
        self.db.add_wishlist(self.wl.entity_id, self.wl.name, self.wl.price, self.wl.url)

        # Check if wishlist is now saved in the db
        self.assertTrue(self.db.is_wishlist_saved(self.wl.entity_id), "Wishlist is not saved in the db!")

    def test_is_product_saved(self):
        """Test to check if is_product_saved method works as intended"""
        # Make sure product is not already saved
        self.assertFalse(self.db.is_product_saved(self.p.entity_id), "Product should not be saved yet!")

        # Add product to the db
        self.db.add_product(self.p.entity_id, self.p.name, self.p.price, self.p.url)

        # Check if product is saved afterwards
        self.assertTrue(self.db.is_product_saved(self.p.entity_id), "Product is not saved in the db!")

    def test_add_wishlist(self):
        """Test for checking if wishlists are being added correctly"""
        # Make sure that element is not already in database
        result = self.db.cursor.execute("SELECT count(*) FROM wishlists WHERE wishlist_id=?", [self.wl.entity_id]).fetchone()[0]
        self.assertEqual(0, result)

        self.db.add_wishlist(wishlist_id=self.wl.entity_id, name=self.wl.name, url=self.wl.url, price=self.wl.price)
        result = self.db.cursor.execute("SELECT wishlist_id, name, url, price  FROM wishlists WHERE wishlist_id=?", [self.wl.entity_id]).fetchone()

        self.assertEqual(self.wl.entity_id, result[0], msg="ID is not equal!")
        self.assertEqual(self.wl.name, result[1], msg="Name is not equal!")
        self.assertEqual(self.wl.url, result[2], msg="Url is not equal!")
        self.assertEqual(self.wl.price, result[3], msg="Price is not equal!")

    def test_add_product(self):
        """Test for checking if products are being added correctly"""
        # Make sure that element is not already in database
        result = self.db.cursor.execute("SELECT count(*) FROM products WHERE product_id=?", [self.p.entity_id]).fetchone()[0]
        self.assertEqual(0, result)

        # Check if product is saved afterwards
        self.db.add_product(product_id=self.p.entity_id, name=self.p.name, url=self.p.url, price=self.p.price)
        result = self.db.cursor.execute("SELECT product_id, name, url, price FROM products WHERE product_id=?", [self.p.entity_id]).fetchone()

        self.assertEqual(result[0], self.p.entity_id, msg="ID is not equal!")
        self.assertEqual(result[1], self.p.name, msg="Name is not equal!")
        self.assertEqual(result[2], self.p.url, msg="Url is not equal!")
        self.assertEqual(result[3], self.p.price, msg="Price is not equal!")

    def test_rm_wishlist(self):
        """Test for checking if removing a wishlist works as intended"""
        # Add wishlist and check if it's in the db
        self.assertFalse(self.db.is_wishlist_saved(self.wl.entity_id))
        self.db.add_wishlist(self.wl.entity_id, self.wl.name, self.wl.price, self.wl.url)
        self.assertTrue(self.db.is_wishlist_saved(self.wl.entity_id))

        # Check if wishlist gets removed properly
        self.db.rm_wishlist(self.wl.entity_id)
        self.assertFalse(self.db.is_wishlist_saved(self.wl.entity_id))

    def test_rm_product(self):
        """Test for checking if removing a product works as intended"""
        # Add product and check if it's in the db
        self.assertFalse(self.db.is_product_saved(self.p.entity_id))
        self.db.add_product(self.p.entity_id, self.p.name, self.p.price, self.p.url)
        self.assertTrue(self.db.is_product_saved(self.p.entity_id))

        # Check if product gets removed properly
        self.db.rm_product(self.p.entity_id)
        self.assertFalse(self.db.is_product_saved(self.p.entity_id))

    def test_subscribe_wishlist(self):
        """Test for checking if subscribing a wishlist works as intended"""
        user_id = 11223344
        first_name = "John"
        last_name = "Doe"
        username = "JohnDoe"

        self.db.add_wishlist(wishlist_id=self.wl.entity_id, name=self.wl.name, url=self.wl.url, price=self.wl.price)
        self.db.add_user(user_id, first_name, last_name, username)

        result = self.db.cursor.execute("SELECT wishlist_id FROM wishlist_subscribers AS ws WHERE ws.user_id=? AND ws.wishlist_id=?;",
                                        [str(user_id), str(self.wl.entity_id)]).fetchone()
        self.assertEqual(result, None)

        self.db.subscribe_wishlist(self.wl.entity_id, user_id)
        result = self.db.cursor.execute("SELECT wishlist_id FROM wishlist_subscribers AS ws WHERE ws.user_id=? AND ws.wishlist_id=?;",
                                        [str(user_id), str(self.wl.entity_id)]).fetchone()

        self.assertEqual(len(result), 1)

    def test_subscribe_product(self):
        """Test for checking if subscribing a product works as intended"""
        user_id = 11223344
        first_name = "John"
        last_name = "Doe"
        username = "JohnDoe"

        self.db.add_product(product_id=self.p.entity_id, name=self.p.name, url=self.p.url, price=self.p.price)
        self.db.add_user(user_id, first_name, last_name, username)

        result = self.db.cursor.execute("SELECT product_id FROM product_subscribers AS ps WHERE ps.user_id=? AND ps.product_id=?;",
                                        [str(user_id), str(self.p.entity_id)]).fetchone()
        self.assertIsNone(result)

        self.db.subscribe_product(self.p.entity_id, user_id)
        result = self.db.cursor.execute("SELECT product_id FROM product_subscribers AS ps WHERE ps.user_id=? AND ps.product_id=?;",
                                        [str(user_id), str(self.p.entity_id)]).fetchone()

        self.assertEqual(len(result), 1)

    def test_unsubscribe_wishlist(self):
        """Test for checking if unsubscribing a wishlist works as intended"""
        user_id = 11223344
        first_name = "John"
        last_name = "Doe"
        username = "JohnDoe"

        self.db.add_wishlist(wishlist_id=self.wl.entity_id, name=self.wl.name, url=self.wl.url, price=self.wl.price)
        self.db.add_user(user_id, first_name, last_name, username)
        self.db.subscribe_wishlist(self.wl.entity_id, user_id)

        result = self.db.cursor.execute("SELECT wishlist_id FROM wishlist_subscribers AS ws WHERE ws.user_id=? AND ws.wishlist_id=?;",
                                        [str(user_id), str(self.wl.entity_id)]).fetchone()
        self.assertEqual(len(result), 1)

        self.db.unsubscribe_wishlist(user_id, self.wl.entity_id)
        result = self.db.cursor.execute("SELECT wishlist_id FROM wishlist_subscribers AS ws WHERE ws.user_id=? AND ws.wishlist_id=?;",
                                        [str(user_id), str(self.wl.entity_id)]).fetchone()

        self.assertIsNone(result)

    def test_unsubscribe_product(self):
        """Test for checking if unsubscribing a product works as intended"""
        user_id = 11223344
        first_name = "John"
        last_name = "Doe"
        username = "JohnDoe"

        self.db.add_product(product_id=self.p.entity_id, name=self.p.name, url=self.p.url, price=self.p.price)
        self.db.add_user(user_id, first_name, last_name, username)
        self.db.subscribe_product(self.p.entity_id, user_id)
        result = self.db.cursor.execute("SELECT product_id FROM product_subscribers AS ps WHERE ps.user_id=? AND ps.product_id=?;",
                                        [str(user_id), str(self.p.entity_id)]).fetchone()
        self.assertEqual(len(result), 1)

        self.db.unsubscribe_product(user_id, self.p.entity_id)
        result = self.db.cursor.execute("SELECT product_id FROM product_subscribers AS ps WHERE ps.user_id=? AND ps.product_id=?;",
                                        [str(user_id), str(self.p.entity_id)]).fetchone()

        self.assertIsNone(result)

    def test_get_user(self):
        """Test to check if getting user information works as intended"""
        # Check that None is returned if no user is saved
        user = self.user

        user_db = self.db.get_user(user.get("user_id"))
        self.assertIsNone(user_db)

        self.db.add_user(user.get("user_id"), user.get("first_name"), user.get("last_name"), user.get("username"), user.get("lang_code"))
        user_db = self.db.get_user(user.get("user_id"))
        self.assertEqual(user.get("user_id"), user_db.user_id)
        self.assertEqual(user.get("first_name"), user_db.first_name)
        self.assertEqual(user.get("last_name"), user_db.last_name)
        self.assertEqual(user.get("username"), user_db.username)
        self.assertEqual(user.get("lang_code"), user_db.lang_code)

    def test_get_userids_for_wishlist(self):
        """Test to check if getting the (subscriber) userid from a wishlist works as intended"""
        # Users should be 0 in the beginning
        users = self.db.get_userids_for_wishlist(self.wl.entity_id)
        self.assertEqual(0, len(users))

        # Add users and wishlist
        user = self.user
        user2 = self.user2

        self.db.add_user(user.get("user_id"), user.get("first_name"), user.get("last_name"), user.get("username"), user.get("lang_code"))
        self.db.add_user(user2.get("user_id"), user2.get("first_name"), user2.get("last_name"), user2.get("username"), user2.get("lang_code"))
        self.db.add_wishlist(self.wl.entity_id, self.wl.name, self.wl.price, self.wl.url)

        # Subscribe user to wishlist
        self.db.subscribe_wishlist(wishlist_id=self.wl.entity_id, user_id=user.get("user_id"))
        users = self.db.get_userids_for_wishlist(self.wl.entity_id)

        # Check if wishlist got one subscriber and it's the correct one
        self.assertEqual(1, len(users))
        self.assertEqual(user.get("user_id"), users[0])

        # Subscribe another user and check if both users are now subscribers
        self.db.subscribe_wishlist(wishlist_id=self.wl.entity_id, user_id=user2.get("user_id"))
        users = self.db.get_userids_for_wishlist(self.wl.entity_id)
        self.assertEqual(2, len(users))

        for user_id in users:
            if user_id != user.get("user_id") and user_id != user2.get("user_id"):
                self.fail("I don't know that userID")

    def test_get_users_for_product(self):
        """Test to check if getting the (subscriber) userid from a wishlist works as intended"""
        # Users should be 0 in the beginning
        users = self.db.get_userids_for_product(self.p.entity_id)
        self.assertEqual(0, len(users))

        # Add users and wishlist
        user = self.user
        user2 = self.user2

        self.db.add_user(user.get("user_id"), user.get("first_name"), user.get("last_name"), user.get("username"), user.get("lang_code"))
        self.db.add_user(user2.get("user_id"), user2.get("first_name"), user2.get("last_name"), user2.get("username"), user2.get("lang_code"))
        self.db.add_product(self.p.entity_id, self.p.name, self.p.price, self.p.url)

        # Subscribe user to wishlist
        self.db.subscribe_product(product_id=self.p.entity_id, user_id=user.get("user_id"))
        users = self.db.get_userids_for_product(self.p.entity_id)

        # Check if wishlist got one subscriber and it's the correct one
        self.assertEqual(1, len(users))
        self.assertEqual(user.get("user_id"), users[0])

        # Subscribe another user and check if both users are now subscribers
        self.db.subscribe_product(product_id=self.p.entity_id, user_id=user2.get("user_id"))
        users = self.db.get_userids_for_product(self.p.entity_id)
        self.assertEqual(2, len(users))

        for user_id in users:
            if user_id != user.get("user_id") and user_id != user2.get("user_id"):
                self.fail("I don't know that userID")

    def test_get_wishlists_for_user(self):
        """Test to check if getting wishlists for a user works as intended"""
        user = self.user

        wl1 = Wishlist(123123, "Wishlist", "https://geizhals.de/?cat=WL-123123", 123.45)
        wl2 = Wishlist(987123, "Wishlist2", "https://geizhals.de/?cat=WL-987123", 1.23)
        wl3 = Wishlist(4567418, "Wishlist3", "https://geizhals.de/?cat=WL-987123", 154.00)
        local_wishlists = [wl1, wl2]

        # Add user
        self.db.add_user(user.get("user_id"), user.get("first_name"), user.get("username"), user.get("lang_code"))

        # Add wishlist1 & wishlist2 & wishlist3
        self.db.add_wishlist(wl1.entity_id, wl1.name, wl1.price, wl1.url)
        self.db.add_wishlist(wl2.entity_id, wl2.name, wl2.price, wl2.url)
        self.db.add_wishlist(wl3.entity_id, wl3.name, wl3.price, wl3.url)

        # Subscribe user to wishlist1 & wishlist2
        self.db.subscribe_wishlist(wl1.entity_id, user.get("user_id"))
        self.db.subscribe_wishlist(wl2.entity_id, user.get("user_id"))

        # Check if wishlists are in the return value
        wishlists = self.db.get_wishlists_for_user(user.get("user_id"))

        # Make sure that both lists are the same length
        self.assertEqual(len(wishlists), len(local_wishlists))

        for local_wishlist in local_wishlists:
            for wishlist in wishlists:
                if wishlist.entity_id == local_wishlist.entity_id:
                    break
            else:
                # Make sure that each subscribed wishlist is in the list
                self.fail("Subscribed wishlist is not in the list")

    def test_get_products_for_user(self):
        """Test to check if getting products for a user works as intended"""
        user = self.user

        p1 = Product(123123, "Product", "https://geizhals.de/?cat=WL-123123", 123.45)
        p2 = Product(987123, "Product2", "https://geizhals.de/?cat=WL-987123", 1.23)
        p3 = Product(4567418, "Product3", "https://geizhals.de/?cat=WL-987123", 154.00)
        local_products = [p1, p2]

        # Add user
        self.db.add_user(user.get("user_id"), user.get("first_name"), user.get("last_name"), user.get("username"), user.get("lang_code"))

        # Add product1 & product2 & product3
        self.db.add_product(p1.entity_id, p1.name, p1.price, p1.url)
        self.db.add_product(p2.entity_id, p2.name, p2.price, p2.url)
        self.db.add_product(p3.entity_id, p3.name, p3.price, p3.url)

        # Subscribe user to product1 & product2
        self.db.subscribe_product(p1.entity_id, user.get("user_id"))
        self.db.subscribe_product(p2.entity_id, user.get("user_id"))

        # Check if products are in the return value
        products = self.db.get_products_for_user(user.get("user_id"))

        # Make sure that both lists are the same length
        self.assertEqual(len(products), len(local_products))

        for local_product in local_products:
            for product in products:
                if product.entity_id == local_product.entity_id:
                    break
            else:
                # Make sure that each subscribed product is in the list
                self.fail("Subscribed product is not in the list")

    def test_is_user_wishlist_subscriber(self):
        """Check if checking for wishlist subscribers works as intended"""
        user1 = self.user
        user2 = self.user2

        wl1 = Wishlist(123123, "Wishlist", "https://geizhals.de/?cat=WL-123123", 123.45)
        wl2 = Wishlist(987123, "Wishlist2", "https://geizhals.de/?cat=WL-987123", 1.23)

        # Add user1, add user2
        self.helper_add_user(user1)
        self.helper_add_user(user2)
        # Add wishlist1, add wishlist2
        self.db.add_wishlist(wl1.entity_id, wl1.name, wl1.price, wl1.url)
        self.db.add_wishlist(wl2.entity_id, wl2.name, wl2.price, wl2.url)

        # subscribe user1 to wishlist1
        self.db.subscribe_wishlist(wl1.entity_id, user1.get("user_id"))

        # subscribe user2 to wishlist2
        self.db.subscribe_wishlist(wl2.entity_id, user2.get("user_id"))

        # check if user1 is subscribed to wishlist1 -> True
        self.assertTrue(self.db.is_user_wishlist_subscriber(user1.get("user_id"), wl1.entity_id))

        # check if user2 is subscribed to wishlist1 -> False
        self.assertFalse(self.db.is_user_wishlist_subscriber(user2.get("user_id"), wl1.entity_id))

        # check if user1 is subscribed to wishlist2 -> False
        self.assertFalse(self.db.is_user_wishlist_subscriber(user1.get("user_id"), wl2.entity_id))

        # check if user2 is subscribed to wishlist2 -> True
        self.assertTrue(self.db.is_user_wishlist_subscriber(user2.get("user_id"), wl2.entity_id))

    def test_is_user_product_subscriber(self):
        """Check if checking for product subscribers works as intended"""
        user1 = self.user
        user2 = self.user2

        p1 = Product(123123, "Product", "https://geizhals.de/?cat=WL-123123", 123.45)
        p2 = Product(987123, "Product2", "https://geizhals.de/?cat=WL-987123", 1.23)

        # Add user1, add user2
        self.helper_add_user(user1)
        self.helper_add_user(user2)
        # Add product1, add product2
        self.db.add_product(p1.entity_id, p1.name, p1.price, p1.url)
        self.db.add_product(p2.entity_id, p2.name, p2.price, p2.url)

        # subscribe user1 to product1
        self.db.subscribe_product(p1.entity_id, user1.get("user_id"))

        # subscribe user2 to product2
        self.db.subscribe_product(p2.entity_id, user2.get("user_id"))

        # check if user1 is subscribed to product1 -> True
        self.assertTrue(self.db.is_user_product_subscriber(user1.get("user_id"), p1.entity_id))

        # check if user2 is subscribed to product1 -> False
        self.assertFalse(self.db.is_user_product_subscriber(user2.get("user_id"), p1.entity_id))

        # check if user1 is subscribed to product2 -> False
        self.assertFalse(self.db.is_user_product_subscriber(user1.get("user_id"), p2.entity_id))

        # check if user2 is subscribed to product2 -> True
        self.assertTrue(self.db.is_user_product_subscriber(user2.get("user_id"), p2.entity_id))

    def test_update_wishlist_name(self):
        """Test to check if updating wishlist names works as intended"""
        self.db.add_wishlist(self.wl.entity_id, self.wl.name, self.wl.price, self.wl.url)
        self.assertEqual(self.db.get_wishlist_info(self.wl.entity_id).name, self.wl.name)

        self.db.update_wishlist_name(self.wl.entity_id, "New Wishlist")
        self.assertEqual(self.db.get_wishlist_info(self.wl.entity_id).name, "New Wishlist")

    def test_update_product_name(self):
        """Test to check if updating product names works as intended"""
        self.db.add_product(self.p.entity_id, self.p.name, self.p.price, self.p.url)
        self.assertEqual(self.db.get_product_info(self.p.entity_id).name, self.p.name)

        self.db.update_product_name(self.p.entity_id, "New Product")
        self.assertEqual(self.db.get_product_info(self.p.entity_id).name, "New Product")

    def test_update_wishlist_price(self):
        """Test to check if updating the wishlist price in the database works as intended"""
        new_price = 999.99
        self.db.add_wishlist(self.wl.entity_id, self.wl.name, self.wl.price, self.wl.url)
        self.db.update_wishlist_price(wishlist_id=self.wl.entity_id, price=new_price)

        price = self.db.cursor.execute("SELECT price FROM wishlists WHERE wishlist_id=?", [self.wl.entity_id]).fetchone()[0]

        self.assertEqual(price, new_price)

    def test_update_product_price(self):
        """Test to check if updating the product price in the database works as intended"""
        new_price = 999.99
        self.db.add_product(self.p.entity_id, self.p.name, self.p.price, self.p.url)
        self.db.update_product_price(product_id=self.p.entity_id, price=new_price)

        price = self.db.cursor.execute("SELECT price FROM products WHERE product_id=?", [self.p.entity_id]).fetchone()[0]

        self.assertEqual(price, new_price)

    def test_get_all_users(self):
        """Test to check if retreiving all users from the database works"""
        users = [{"user_id": 415641, "first_name": "Peter", "last_name": "Müller", "username": "name2", "lang_code": "en_US"},
                 {"user_id": 564864654, "first_name": "asdf", "last_name": "jhkasd", "username": "AnotherUser", "lang_code": "en_US"},
                 {"user_id": 54564162, "first_name": "NoName", "last_name": "123iuj", "username": "Metallica", "lang_code": "en_US"},
                 {"user_id": 5555333, "first_name": "1234", "last_name": "koldfg", "username": "d_Rickyy_b", "lang_code": "en_US"}]

        # Check that database is empty
        all_users_db = self.db.get_all_users()
        self.assertEqual(len(all_users_db), 0, msg="There are already users in the db!")

        for user in users:
            self.helper_add_user(user)

        all_users_db = self.db.get_all_users()

        self.assertEqual(len(all_users_db), len(users), msg="Users in database is not same amount as users in test!")

        for db_user in all_users_db:
            for user in users:
                if user.get("user_id") == db_user.get("user_id"):
                    self.assertEqual(user.get("first_name"), db_user.get("first_name"))
                    self.assertEqual(user.get("username"), db_user.get("username"))
                    self.assertEqual(user.get("lang_code"), db_user.get("lang_code"))
                    break
            else:
                self.fail("User not found!")

    def test_get_all_subscribers(self):
        self.assertEqual([], self.db.get_all_subscribers(), msg="Initial user list not empty!")

        self.db.add_user(12345, "Test", "lastName", "User")
        self.db.add_user(54321, "Test2", "lastName2", "User2")
        self.assertEqual([], self.db.get_all_subscribers(), msg="User list not empty although no subscribers!")

        self.db.add_product(1, "Testproduct", 30, "https://example.com")
        self.db.subscribe_product(1, 12345)
        self.assertEqual([12345], self.db.get_all_subscribers(), msg="User list still empty although product subscription!")

        self.db.add_wishlist(333, "Wishlist", 15, "https://example.com/wishlist")
        self.db.subscribe_wishlist(333, 54321)
        self.assertEqual(2, len(self.db.get_all_subscribers()), msg="User list missing user although wishlist subscription!")
        self.assertEqual([12345, 54321], self.db.get_all_subscribers(), msg="User list missing user although wishlist subscription!")

        self.db.subscribe_product(1, 54321)
        self.assertEqual(2, len(self.db.get_all_subscribers()), msg="User counting multiple times after product subscription!")
        self.assertEqual([12345, 54321], self.db.get_all_subscribers(), msg="User counting multiple times after product subscription!")

    def test_get_lang_id(self):
        """Test to check if receiving the lang_code works"""
        user = self.user

        # Check that user does not already exist
        user_db = self.db.get_user(user.get("user_id"))
        self.assertEqual(user_db, None)

        # Add user to database
        self.helper_add_user(user)

        lang_id = self.db.get_lang_id(user.get("user_id"))
        self.assertEqual(lang_id, user.get("lang_code"))

        # Trying a random user_id that is not stored yet
        self.assertEqual(self.db.get_lang_id(19283746), "en")

    def test_add_user(self):
        """Test to check if adding users works as expected"""
        user = {"user_id": 123456, "first_name": "John", "username": "testUsername", "lang_code": "en_US"}

        # Check that user does not already exist
        user_db = self.db.get_user(user.get("user_id"))
        self.assertEqual(user_db, None)

        # Add user to database
        self.helper_add_user(user)

        # Check if user was added
        user_db = self.db.get_user(user.get("user_id"))
        self.assertEqual(user_db.user_id, user.get("user_id"))

        # Test default value of lang_code
        user2 = {"user_id": 4321, "first_name": "Peter", "username": "AsDf", "lang_code": "en_US"}
        self.db.add_user(user_id=user2.get("user_id"), first_name=user2.get("first_name"), last_name=user2.get("last_name"), username=user2.get("username"))
        user_db2 = self.db.get_user(user2.get("user_id"))
        self.assertEqual("de-DE", user_db2.lang_code)

    def test_delete_user(self):
        """Test to check if users (and their wishlists/products) are properly deleted"""
        user = {"user_id": 123456, "first_name": "John", "username": "testUsername", "lang_code": "en_US"}
        user_id = user.get("user_id")

        # Add user to the database
        self.db.add_user(user.get("user_id"), user.get("first_name"), user.get("username"), user.get("lang_code"))

        # Add product and wishlist to the database
        self.db.add_product(self.p.entity_id, self.p.name, self.p.price, self.p.url)
        self.db.add_wishlist(self.wl.entity_id, self.wl.name, self.wl.price, self.wl.url)

        # Subscribe to the product and to the wishlist
        self.db.subscribe_wishlist(self.wl.entity_id, user_id)
        self.db.subscribe_product(self.p.entity_id, user_id)

        # Make sure subscriber count = 1
        wl_count = self.db.get_subscribed_wishlist_count(user_id)
        self.assertEqual(1, wl_count, "Subscribed wishlists should be 1 but is not!")

        p_count = self.db.get_subscribed_product_count(user_id)
        self.assertEqual(1, p_count, "Subscribed products should be 1 but is not!")

        wl_subs = self.db.cursor.execute("SELECT count(*) FROM wishlist_subscribers;").fetchone()[0]
        self.assertEqual(1, wl_subs)

        p_subs = self.db.cursor.execute("SELECT count(*) FROM product_subscribers;").fetchone()[0]
        self.assertEqual(1, p_subs)

        # Delete user
        self.db.delete_user(user_id)

        # Make sure the product and the wishlist still exist
        wishlist = self.db.get_wishlist_info(self.wl.entity_id)
        self.assertIsNotNone(wishlist)

        product = self.db.get_product_info(self.p.entity_id)
        self.assertIsNotNone(product)

        db_user = self.db.get_user(user_id)
        self.assertIsNone(db_user)

        # Make sure the user is no longer subscribed
        wl_subs = self.db.cursor.execute("SELECT count(*) FROM wishlist_subscribers;").fetchone()[0]
        self.assertEqual(0, wl_subs)

        p_subs = self.db.cursor.execute("SELECT count(*) FROM product_subscribers;").fetchone()[0]
        self.assertEqual(0, p_subs)

    def test_is_user_saved(self):
        """Test to check if the 'check if a user exists' works as expected"""
        user = {"user_id": 123456, "first_name": "John", "username": "testUsername", "lang_code": "en_US"}

        # Check that user does not already exist
        user_db = self.db.get_user(user.get("user_id"))
        self.assertIsNone(user_db, "User is not None!")
        self.assertFalse(self.db.is_user_saved(user.get("user_id")))

        self.db.add_user(user.get("user_id"), user.get("first_name"), user.get("username"), user.get("lang_code"))

        self.assertTrue(self.db.is_user_saved(user.get("user_id")))
