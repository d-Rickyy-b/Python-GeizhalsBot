"""Core file for the business logic to interact with the backend"""
# -*- coding: utf-8 -*-

import re

from database.db_wrapper import DBwrapper
from geizhals.entity import EntityType
from geizhals.product import Product
from geizhals.wishlist import Wishlist
from util.exceptions import AlreadySubscribedException, WishlistNotFoundException, ProductNotFoundException, \
    InvalidURLException


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


def add_product_if_new(product):
    """Save a product to the database, if it is not already stored"""
    db = DBwrapper.get_instance()

    if not db.is_product_saved(product.id):
        db.add_product(product.id, product.name, product.price, product.url)
    else:
        pass


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


def subscribe_product(user, product):
    """Subscribe to a product as a user"""
    db = DBwrapper.get_instance()

    if not db.is_user_product_subscriber(user.id, product.id):
        db.subscribe_product(product.id, user.id)
    else:
        raise AlreadySubscribedException


def subscribe_entity(user, entity):
    db = DBwrapper.get_instance()
    if entity.TYPE == EntityType.WISHLIST:
        if not db.is_user_wishlist_subscriber(user.id, entity.id):
            db.subscribe_wishlist(entity.id, user.id)
        else:
            raise AlreadySubscribedException
    elif entity.TYPE == EntityType.PRODUCT:
        if not db.is_user_product_subscriber(user.id, entity.id):
            db.subscribe_product(entity.id, user.id)
        else:
            raise AlreadySubscribedException
    else:
        raise ValueError("Unknown EntityType")


def get_wishlist(id):
    """Returns the wishlist object for an id"""
    db = DBwrapper.get_instance()
    wishlist = db.get_wishlist_info(id)

    if wishlist is None:
        raise WishlistNotFoundException

    return wishlist


def get_product(id):
    """Returns the product object for an id"""
    db = DBwrapper.get_instance()
    product = db.get_product_info(id)

    if product is None:
        raise ProductNotFoundException

    return product


def get_wishlist_count(user_id):
    """Returns the count of subscribed wishlists for a user"""
    db = DBwrapper.get_instance()
    return db.get_subscribed_wishlist_count(user_id)


def get_product_count(user_id):
    db = DBwrapper.get_instance()
    return db.get_subscribed_product_count(user_id)


def get_wishlists_for_user(user_id):
    """Returns the subscribed wishlists for a certain user"""
    db = DBwrapper.get_instance()
    return db.get_wishlists_for_user(user_id)


def get_products_for_user(user_id):
    """Returns the subscribed wishlists for a certain user"""
    db = DBwrapper.get_instance()
    return db.get_products_for_user(user_id)


def get_user_by_id(user_id):
    db = DBwrapper.get_instance()
    return db.get_user(user_id)


def get_wl_url(text):
    if re.match(Wishlist.url_pattern, text):
        return text
    else:
        raise InvalidURLException


def get_p_url(text):
    if re.match(Product.url_pattern, text):
        return text
    else:
        raise InvalidURLException


def get_entity_subscribers(entity):
    """Returns the subscribers of an entity"""
    db = DBwrapper.get_instance()
    if entity.TYPE == EntityType.WISHLIST:
        return db.get_users_for_wishlist(entity.id)
    elif entity.TYPE == EntityType.PRODUCT:
        return db.get_users_for_product(entity.id)
    else:
        raise ValueError("Unknown EntityType")


def update_entity_price(entity, price):
    """Update the price of an entity"""
    db = DBwrapper.get_instance()
    if entity.TYPE == EntityType.WISHLIST:
        db.update_wishlist_price(entity.id, price)
    elif entity.TYPE == EntityType.PRODUCT:
        db.update_product_price(entity.id, price)
    else:
        raise ValueError("Unknown EntityType")


def update_entity_name(entity, name):
    """Update the name of an entity"""
    db = DBwrapper.get_instance()
    if entity.TYPE == EntityType.WISHLIST:
        db.update_wishlist_name(entity.id, name)
    elif entity.TYPE == EntityType.PRODUCT:
        db.update_product_name(entity.id, name)
    else:
        raise ValueError("Unknown EntityType")
