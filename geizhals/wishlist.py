# -*- coding: utf-8 -*-
import re

import geizhals.core
import geizhals.exceptions
from geizhals.entity import Entity, EntityType


class Wishlist(Entity):
    """Representation of a Geizhals wishlist"""
    url_pattern = r"https:\/\/geizhals\.(de|at|eu)\/\?cat=WL-([0-9]+)"
    ENTITY_NAME = "Wunschliste"
    TYPE = EntityType.WISHLIST

    @staticmethod
    def from_url(url):
        """Create a wishlist object by url"""
        if not re.match(Wishlist.url_pattern, url):
            raise geizhals.exceptions.InvalidWishlistURLException

        wl = Wishlist(id=0, name="", url=url, price=0)
        wl.price = wl.get_current_price()
        wl.name = wl.get_current_name()
        wl.id = int(re.search(Wishlist.url_pattern, url).group(2))

        return wl

    def get_wishlist_products(self):
        raise NotImplementedError("get_wishlist_products is not implemented yet")
