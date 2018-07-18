# -*- coding: utf-8 -*-
import re

import geizhals.core
import geizhals.exceptions
from geizhals import Entity, EntityType


class Product(Entity):
    """Representation of a Geizhals product"""
    url_pattern = "https:\/\/geizhals\.(de|at|eu)\/[0-9a-zA-Z\-]*a([0-9]+).html"
    ENTITY_NAME = "Produkt"
    TYPE = EntityType.PRODUCT

    @staticmethod
    def from_url(url):
        if not re.match(Product.url_pattern, url):
            raise geizhals.exceptions.InvalidWishlistURLException

        p = Product(id=0, name="", url=url, price=0)
        p.price = p.get_current_price()
        p.name = p.get_current_name()
        p.id = int(re.search(Product.url_pattern, url).group(2))

        return p
