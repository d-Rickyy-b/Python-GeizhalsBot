# -*- coding: utf-8 -*-

import os
import unittest
import geizhals.core


class GeizhalsCoreTest(unittest.TestCase):
    dir_path = os.path.dirname(os.path.abspath(__file__))
    test_file_path = os.path.join(dir_path, "test.html")

    def setUp(self):
        with open(self.test_file_path, "r") as f:
            self.html = f.read()

    def tearDown(self):
        pass

    def test_parse_wishlist_price(self):
        price = geizhals.core.parse_wishlist_price(self.html)
        self.assertEqual(price, "717.81")

    def test_parse_wishlist_name(self):
        name = geizhals.core.parse_wishlist_name(self.html)
        self.assertEqual(name, "NAS")


