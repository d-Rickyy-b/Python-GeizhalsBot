# -*- coding: utf-8 -*-


import unittest

from geizhals.util.ringbuffer import Ringbuffer


class RingbufferTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_next_proxy(self):
        elements = ['Test', '1', 'example3']
        rb = Ringbuffer(elements)

        self.assertEqual(len(rb), len(elements))

        e1 = rb.next()
        i1 = elements.index(e1)

        e2 = rb.next()
        i2 = elements.index(e2)

        e3 = rb.next()
        i3 = elements.index(e3)

        e4 = rb.next()
        i4 = elements.index(e4)

        e5 = rb.next()
        i5 = elements.index(e5)

        e6 = rb.next()
        i6 = elements.index(e6)

        self.assertEqual(i4, i1)
        self.assertEqual(e4, e1)
        self.assertEqual(i5, i2)
        self.assertEqual(e5, e2)
        self.assertEqual(i6, i3)
        self.assertEqual(e6, e3)

        self.assertEqual(len(rb), len(elements))
