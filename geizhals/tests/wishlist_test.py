# -*- coding: utf-8 -*-

import unittest

from geizhals.exceptions import InvalidWishlistURLException
from geizhals import Wishlist


class WishlistTest(unittest.TestCase):

    def setUp(self):
        self.wl = Wishlist(id=676328, 
                           name="NAS", 
                           url="https://geizhals.de/?cat=WL-676328", 
                           price=617.90)

    def tearDown(self):
        del self.wl

    def test_from_url(self):
        """Test to check if creating a wishlist by url works as intended"""
        # Create a wishlist by url - needs a network connection
        my_wl = Wishlist.from_url(self.wl.url)

        self.assertEqual(type(my_wl), Wishlist)

        self.assertEqual(my_wl.id, self.wl.id)
        self.assertEqual(my_wl.name, self.wl.name)
        self.assertEqual(my_wl.url, self.wl.url)

        # The price obviously can't be checked by a precise value
        self.assertEqual(type(my_wl.price), float)
        self.assertGreater(my_wl.price, 0.1)

        # Make sure that wrong urls lead to exceptions
        with self.assertRaises(InvalidWishlistURLException):
            failed_wl = Wishlist.from_url("http://example.com")

    def test_get_wishlist_products(self):
        """Test to check if getting the products of a wishlist works as intended"""
        # Since this is not implemented yet, there should be a exception
        with self.assertRaises(NotImplementedError):
            products = self.wl.get_wishlist_products()
