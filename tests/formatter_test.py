# -*- coding: utf-8 -*-

import unittest

import formatter


class FormatterTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_bold(self):
        text = "This is a Text"
        expected = "<b>This is a Text</b>"

        self.assertEqual(formatter.bold(text), expected, "Text does not match expected bold string!")

    def test_link(self):
        text = "name"
        link = "www.example.com"

        self.assertEqual(formatter.link(link, text), "<a href=\"www.example.com\">name</a>")

    def test_price(self):
        price_pos = 1.752221
        price_neg = -1.82111

        self.assertEqual(formatter.price(price_pos), "+1.75 €", msg="Positive price not displayed correctly")
        self.assertEqual(formatter.price(price_neg), "-1.82 €", msg="Negative price not displayed correctly")
