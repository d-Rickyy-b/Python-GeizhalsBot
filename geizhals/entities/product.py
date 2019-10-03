# -*- coding: utf-8 -*-
import re
import logging

import geizhals.core
import geizhals.exceptions
from geizhals.entities import Entity, EntityType

logger = logging.getLogger(__name__)


class Product(Entity):
    """Representation of a Geizhals product"""
    url_pattern = r"https:\/\/geizhals\.(de|at|eu)\/[0-9a-zA-Z\-]*a([0-9]+).html"
    ENTITY_NAME = "Produkt"
    TYPE = EntityType.PRODUCT

    @staticmethod
    def from_url(url):
        if not re.match(Product.url_pattern, url):
            raise geizhals.exceptions.InvalidWishlistURLException

        p = Product(entity_id=0, name="", url=url, price=0)
        p.price = p.get_current_price()
        p.name = p.get_current_name()
        p.entity_id = int(re.search(Product.url_pattern, url).group(2))

        logger.info("Name: {}".format(p.name))
        logger.info("Price: {}".format(p.price))
        logger.info("Id: {}".format(p.entity_id))

        return p
