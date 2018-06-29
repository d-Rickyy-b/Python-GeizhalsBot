"""Collection of all the exceptions"""


# -*- coding: utf-8 -*-


class AlreadySubscribedException(Exception):
    pass


class WishlistNotFoundException(Exception):
    pass


class ProductNotFoundException(Exception):
    pass


class TooManyWishlistsException(Exception):
    pass


class IncompleteRequestException(Exception):
    pass


class InvalidURLException(Exception):
    pass
