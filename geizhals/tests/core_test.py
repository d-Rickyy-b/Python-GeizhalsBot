# -*- coding: utf-8 -*-

import os
import re
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

    def test_send_request(self):
        """Test to check if downloading the html code of a website works"""
        regex = re.compile(r'\s')
        html = geizhals.core.send_request("http://example.com")
        example_path = os.path.join(self.dir_path, "example.html")

        with open(example_path, "r") as f:
            example_html = f.read()

        # Replace all the whitespace to not have any issue with too many or little of them.
        self.assertEqual(regex.sub("", html), regex.sub("", example_html))

    def test_parse_wishlist_price(self):
        price = geizhals.core.parse_wishlist_price(self.html)
        self.assertEqual(price, "717.81")

    def test_parse_wishlist_name(self):
        name = geizhals.core.parse_wishlist_name(self.html)
        self.assertEqual(name, "NAS")
