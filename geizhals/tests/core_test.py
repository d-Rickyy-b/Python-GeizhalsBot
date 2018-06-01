# -*- coding: utf-8 -*-

import unittest
import geizhals.core


class Test(unittest.TestCase):

    def setUp(self):
        with open("test.html", "r") as f:
            self.html = f.read()

    def tearDown(self):
        pass

    def test_parse_wishlist_price(self):
        price = geizhals.core.parse_wishlist_price(self.html)
        self.assertEqual(price, "717.81")

    def test_parse_wishlist_name(self):
        name = geizhals.core.parse_wishlist_name(self.html)
        self.assertEqual(name, "NAS")


