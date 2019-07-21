"""Collection of all the geizhals exceptions"""


# -*- coding: utf-8 -*-


class InvalidWishlistURLException(Exception):
    pass


class InvalidProductURLException(Exception):
    pass


class HTTPLimitedException(Exception):
    pass
