"""Core file for the business logic to interact with the backend"""
# -*- coding: utf-8 -*-

import re

from database.db_wrapper import DBwrapper
from util.exceptions import AlreadySubscribedException, WishlistNotFoundException, IncompleteRequestException, InvalidURLException
from geizhals.wishlist import Wishlist


def add_user_if_new(user):
    """Save a user to the database, if the user is not already stored"""
    db = DBwrapper.get_instance()
    if not db.is_user_saved(user.id):
        db.add_user(user.id, user.first_name, user.username, user.lang_code)


def add_wishlist_if_new(wishlist):
    """Save a wishlist to the database, if it is not already stored"""
    db = DBwrapper.get_instance()

    if not db.is_wishlist_saved(wishlist.id):
        # logger.debug("URL not in database!")
        db.add_wishlist(wishlist.id, wishlist.name, wishlist.price, wishlist.url)
    else:
        pass
        # logger.debug("URL in database!")


def is_user_wishlist_subscriber(user, wishlist):
    """Returns if a user is a wishlist subscriber"""
    db = DBwrapper.get_instance()

    return db.is_user_wishlist_subscriber(user.id, wishlist.id)


def subscribe_wishlist(user, wishlist):
    """Subscribe to a  wishlist as a user"""
    db = DBwrapper.get_instance()

    if not db.is_user_wishlist_subscriber(user.id, wishlist.id):
        db.subscribe_wishlist(wishlist.id, user.id)
    else:
        raise AlreadySubscribedException


def subscribe_product():
    """Subscribe to a product as a user"""
    pass


def get_wishlist(id):
    """Returns the wishlist object for an id"""
    db = DBwrapper.get_instance()
    wishlist = db.get_wishlist_info(id)

    if wishlist is None:
        raise WishlistNotFoundException

    return wishlist


def get_wishlist_count(user_id):
    """Returns the count of subscribed wishlists for a user"""
    db = DBwrapper.get_instance()

    return db.get_subscribed_wishlist_count(user_id)


def get_wishlists_for_user(user_id):
    """Returns the subscribed wishlists for a certain user"""
    db = DBwrapper.get_instance()
    return db.get_wishlists_for_user(user_id)


def get_url(text):
    if re.match(Wishlist.url_pattern, text):
        return text

    if text == "/add" or text == "Neue Liste":
        raise IncompleteRequestException
    elif "/add " in text:
        url = text.split()[1]
    else:
        raise InvalidURLException

    return url
