# -*- coding: utf-8 -*-
import re
from enum import Enum

import geizhals.core


class Entity(object):
    TYPE = None

    def __init__(self, id: int, name: str, url: str, price: float):
        self.__html = None
        self.id = int(id)
        self.name = str(name)
        self.url = str(url)
        self.price = float(price)

    def get_html(self):
        """Check if html for entity is already downloaded - if not download html and save in self.__html"""
        if not self.__html:
            self.__html = geizhals.core.send_request(self.url)

    def get_current_name(self):
        """Get the current name of an entity from Geizhals"""
        self.get_html()

        name = geizhals.core.parse_entity_name(self.__html, self.TYPE)

        return name

    def get_current_price(self):
        """Get the current price of a wishlist from Geizhals"""
        self.get_html()
        self.get_current_name()
        price = geizhals.core.parse_entity_price(self.__html, self.TYPE)

        # Parse price so that it's a proper comma value (no `,--`)
        pattern = "([0-9]+)\.([0-9]+|[-]+)"
        pattern_dash = "([0-9]+)\.([-]+)"

        if re.match(pattern, price):
            if re.match(pattern_dash, price):
                price = float(re.search(pattern_dash, price).group(1))
        else:
            raise ValueError("Couldn't parse price!")

        return float(price)


class EntityType(Enum):
    WISHLIST = 1
    PRODUCT = 2
