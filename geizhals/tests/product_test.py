# -*- coding: utf-8 -*-

import unittest

from geizhals.exceptions import InvalidWishlistURLException
from geizhals import Product


class ProductTest(unittest.TestCase):

    def setUp(self):
        self.p = Product(id=1756905, 
                         name="Samsung SSD 860 EVO 1TB, SATA (MZ-76E1T0B)",
                         url="https://geizhals.de/samsung-ssd-860-evo-1tb-mz-76e1t0b-a1756905.html", 
                         price=195.85)

    def tearDown(self):
        del self.p

    # Depending on the environment this test might fail and that's okay
    @unittest.expectedFailure
    def test_from_url(self):
        """Test to check if creating a product by url works as intended"""
        # Create a product by url - needs a network connection
        my_p = Product.from_url(self.p.url)

        self.assertEqual(type(my_p), Product)

        self.assertEqual(my_p.id, self.p.id)
        self.assertEqual(my_p.name, self.p.name)
        self.assertEqual(my_p.url, self.p.url)

        # The price obviously can't be checked by a precise value
        self.assertEqual(type(my_p.price), float)
        self.assertGreater(my_p.price, 0.1)

        # Make sure that wrong urls lead to exceptions
        with self.assertRaises(InvalidWishlistURLException):
            failed_p = Product.from_url("http://example.com")
