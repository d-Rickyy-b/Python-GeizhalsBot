# -*- coding: utf-8 -*-

import os
import re
import unittest

import geizhals.core
from geizhals.entity import EntityType


class GeizhalsCoreTest(unittest.TestCase):
    dir_path = os.path.dirname(os.path.abspath(__file__))
    test_wl_file_path = os.path.join(dir_path, "test_wishlist.html")
    test_p_file_path = os.path.join(dir_path, "test_product.html")

    def setUp(self):
        with open(self.test_wl_file_path, "r", encoding='utf8') as f:
            self.html_wl = f.read()

        with open(self.test_p_file_path, "r", encoding='utf8') as f:
            self.html_p = f.read()

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

    def test_parse_entity_price(self):
        """Test to check if parsing prices of entities works"""
        price = geizhals.core.parse_entity_price(self.html_wl, EntityType.WISHLIST)
        self.assertEqual(price, "717.81")

        price = geizhals.core.parse_entity_price(self.html_p, EntityType.PRODUCT)
        self.assertEqual(price, "199.65")

        with self.assertRaises(ValueError):
            geizhals.core.parse_entity_price("Test", "WrongEntityType")

        with self.assertRaises(ValueError):
            geizhals.core.parse_entity_price("Test", None)

    def test_parse_entity_name(self):
        """Test to check if parsing names of entities works"""
        name = geizhals.core.parse_entity_name(self.html_wl, EntityType.WISHLIST)
        self.assertEqual(name, "NAS")

        name = geizhals.core.parse_entity_name(self.html_p, EntityType.PRODUCT)
        self.assertEqual(name, "Samsung SSD 860 EVO 1TB, SATA (MZ-76E1T0B/EU / MZ-76E1T0E)")

        with self.assertRaises(ValueError):
            geizhals.core.parse_entity_name("Test", "WrongEntityType")

        with self.assertRaises(ValueError):
            geizhals.core.parse_entity_name("Test", None)
