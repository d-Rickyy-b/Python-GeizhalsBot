# -*- coding: utf-8 -*-

import unittest

from geizhals.state_handler import GeizhalsStateHandler


class GeizhalsStateHandlerTest(unittest.TestCase):

    def setUp(self):
        self.sh = GeizhalsStateHandler()

    def tearDown(self):
        """Reset the instance so that a new clean instance gets created for each test"""
        GeizhalsStateHandler._instance = None
        GeizhalsStateHandler._initialized = False

    def test_singleton(self):
        """
        Make sure that all objects created from the GeizhalsStateHandler
        class are actually the same object
        """
        self.assertEqual(self.sh, GeizhalsStateHandler())
        self.assertEqual(self.sh, GeizhalsStateHandler())
        self.assertEqual(self.sh, GeizhalsStateHandler())

    def test_get_next_proxy(self):
        # Reset statehandler
        GeizhalsStateHandler._instance = None
        GeizhalsStateHandler._initialized = False
        proxies = ['https://example.com', 'https://test.org', 'http://proxy.net']
        self.sh = GeizhalsStateHandler(use_proxies=True, proxies=proxies)

        self.assertEqual(len(self.sh.proxies), len(proxies))

        p1 = self.sh.get_next_proxy()
        i1 = proxies.index(p1)

        p2 = self.sh.get_next_proxy()
        i2 = proxies.index(p2)

        p3 = self.sh.get_next_proxy()
        i3 = proxies.index(p3)

        p4 = self.sh.get_next_proxy()
        i4 = proxies.index(p4)

        p5 = self.sh.get_next_proxy()
        i5 = proxies.index(p5)

        p6 = self.sh.get_next_proxy()
        i6 = proxies.index(p6)

        self.assertEqual(i4, i1)
        self.assertEqual(p4, p1)
        self.assertEqual(i5, i2)
        self.assertEqual(p5, p2)
        self.assertEqual(i6, i3)
        self.assertEqual(p6, p3)
