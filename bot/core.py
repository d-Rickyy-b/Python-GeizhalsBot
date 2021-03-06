"""Core file for the business logic to interact with the backend"""
# -*- coding: utf-8 -*-

import re

from database.db_wrapper import DBwrapper
from geizhals.entities import EntityType, Product, Wishlist
from util.exceptions import AlreadySubscribedException, WishlistNotFoundException, ProductNotFoundException, \
    InvalidURLException


def add_user_if_new(user):
    """Save a user to the database, if the user is not already stored"""
    db = DBwrapper.get_instance()
    if not db.is_user_saved(user.user_id):
        db.add_user(user_id=user.user_id, first_name=user.first_name, last_name=user.last_name, username=user.username, lang_code=user.lang_code)


def add_wishlist_if_new(wishlist):
    """Save a wishlist to the database, if it is not already stored"""
    db = DBwrapper.get_instance()

    if not db.is_wishlist_saved(wishlist.entity_id):
        # logger.debug("URL not in database!")
        db.add_wishlist(wishlist.entity_id, wishlist.name, wishlist.price, wishlist.url)
    else:
        pass
        # logger.debug("URL in database!")


def add_product_if_new(product):
    """Save a product to the database, if it is not already stored"""
    db = DBwrapper.get_instance()

    if not db.is_product_saved(product.entity_id):
        db.add_product(product.entity_id, product.name, product.price, product.url)
    else:
        pass


def add_entity_if_new(entity):
    db = DBwrapper.get_instance()
    if entity.TYPE == EntityType.WISHLIST:
        if db.is_wishlist_saved(entity.entity_id):
            return
        db.add_wishlist(entity.entity_id, entity.name, entity.price, entity.url)
    elif entity.TYPE == EntityType.PRODUCT:
        if db.is_product_saved(entity.entity_id):
            return
        db.add_product(entity.entity_id, entity.name, entity.price, entity.url)
    else:
        raise ValueError("Unknown EntityType")


def is_user_wishlist_subscriber(user, wishlist):
    """Returns if a user is a wishlist subscriber"""
    db = DBwrapper.get_instance()

    return db.is_user_wishlist_subscriber(user.user_id, wishlist.entity_id)


def subscribe_entity(user, entity):
    """Subscribe to an entity as a user"""
    db = DBwrapper.get_instance()
    if entity.TYPE == EntityType.WISHLIST:
        if not db.is_user_wishlist_subscriber(user.user_id, entity.entity_id):
            db.subscribe_wishlist(entity.entity_id, user.user_id)
        else:
            raise AlreadySubscribedException
    elif entity.TYPE == EntityType.PRODUCT:
        if not db.is_user_product_subscriber(user.user_id, entity.entity_id):
            db.subscribe_product(entity.entity_id, user.user_id)
        else:
            raise AlreadySubscribedException
    else:
        raise ValueError("Unknown EntityType")


def unsubscribe_entity(user, entity):
    db = DBwrapper.get_instance()
    if entity.TYPE == EntityType.WISHLIST:
        db.unsubscribe_wishlist(user.user_id, entity.entity_id)
    elif entity.TYPE == EntityType.PRODUCT:
        db.unsubscribe_product(user.user_id, entity.entity_id)
    else:
        raise ValueError("Unknown EntityType")


def get_all_entities():
    """Returns all the entities in the database"""
    db = DBwrapper.get_instance()
    wishlists = db.get_all_wishlists()
    products = db.get_all_products()

    entities = wishlists + products

    return entities


def get_all_entities_with_subscribers():
    """Returns all the entities with subscribers in the database"""
    db = DBwrapper.get_instance()
    wishlists = db.get_all_subscribed_wishlists()
    products = db.get_all_subscribed_products()

    entities = wishlists + products

    return entities


def get_all_wishlists_with_subscribers():
    db = DBwrapper.get_instance()
    return db.get_all_subscribed_wishlists()


def get_all_products_with_subscribers():
    db = DBwrapper.get_instance()
    return db.get_all_subscribed_products()


def get_wishlist(wishlist_id):
    """Returns the wishlist object for an product_id"""
    db = DBwrapper.get_instance()
    wishlist = db.get_wishlist_info(wishlist_id)

    if wishlist is None:
        raise WishlistNotFoundException

    return wishlist


def get_product(product_id):
    """Returns the product object for an product_id"""
    db = DBwrapper.get_instance()
    product = db.get_product_info(product_id)

    if product is None:
        raise ProductNotFoundException

    return product


def get_entity(entity_id, entity_type):
    if entity_type == EntityType.PRODUCT:
        return get_product(product_id=entity_id)
    elif entity_type == EntityType.WISHLIST:
        return get_wishlist(wishlist_id=entity_id)
    else:
        raise ValueError("Unknown EntityType")


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


def get_e_url(text, entity_type):
    if entity_type == EntityType.WISHLIST:
        if re.match(Wishlist.url_pattern, text):
            return text
    elif entity_type == EntityType.PRODUCT:
        if re.match(Product.url_pattern, text):
            return text

    raise InvalidURLException


def get_type_by_url(text):
    if re.match(Wishlist.url_pattern, text):
        return EntityType.WISHLIST
    elif re.match(Product.url_pattern, text):
        return EntityType.PRODUCT
    else:
        raise InvalidURLException


def get_entity_subscribers(entity):
    """Returns the subscribers of an entity"""
    db = DBwrapper.get_instance()
    if entity.TYPE == EntityType.WISHLIST:
        return db.get_userids_for_wishlist(entity.entity_id)
    elif entity.TYPE == EntityType.PRODUCT:
        return db.get_userids_for_product(entity.entity_id)
    else:
        raise ValueError("Unknown EntityType")


def update_entity_price(entity, price):
    """Update the price of an entity"""
    db = DBwrapper.get_instance()
    if entity.TYPE == EntityType.WISHLIST:
        db.update_wishlist_price(entity.entity_id, price)
    elif entity.TYPE == EntityType.PRODUCT:
        db.update_product_price(entity.entity_id, price)
    else:
        raise ValueError("Unknown EntityType")


def update_entity_name(entity, name):
    """Update the name of an entity"""
    db = DBwrapper.get_instance()
    if entity.TYPE == EntityType.WISHLIST:
        db.update_wishlist_name(entity.entity_id, name)
    elif entity.TYPE == EntityType.PRODUCT:
        db.update_product_name(entity.entity_id, name)
    else:
        raise ValueError("Unknown EntityType")


def rm_entity(entity):
    db = DBwrapper.get_instance()
    if entity.TYPE == EntityType.WISHLIST:
        db.rm_wishlist(entity.entity_id)
    elif entity.TYPE == EntityType.PRODUCT:
        db.rm_product(entity.entity_id)
    else:
        raise ValueError("Unknown EntityType")


def get_price_history(entity, weeks=4):
    db = DBwrapper.get_instance()
    if entity.TYPE == EntityType.WISHLIST:
        return db.get_wishlist_price_history(entity.entity_id, weeks)
    elif entity.TYPE == EntityType.PRODUCT:
        return db.get_product_price_history(entity.entity_id, weeks)


def get_price_count():
    db = DBwrapper.get_instance()
    p_c = db.get_product_pricecount()
    wl_c = db.get_wishlist_pricecount()

    return p_c + wl_c


def delete_user(user_id):
    db = DBwrapper.get_instance()
    db.delete_user(user_id)


def get_all_subscribers():
    db = DBwrapper.get_instance()
    return db.get_all_subscribers()


def get_all_users():
    db = DBwrapper.get_instance()
    return db.get_all_users()
