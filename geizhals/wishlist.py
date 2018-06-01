# -*- coding: utf-8 -*-
import re
import geizhals.core


class Wishlist(object):
    """Representation of a Geizhals wishlist"""

    def __init__(self, id, name, url, price):
        """Create a wishlist object by parameters"""
        self.__html = None
        self.__url = str(url)
        self.__id = int(id)
        self.__name = str(name)
        self.__price = float(price)

    @staticmethod
    def from_url(url):
        """Create a wishlist object by url"""
        url_pattern = "https:\/\/geizhals\.(de|at|eu)\/\?cat=WL-([0-9]+)"

        wl = Wishlist(0, "", url, 0)
        wl.price = wl.get_current_price()
        wl.name = wl.get_current_name()
        wl.id = int(re.search(url_pattern, url).group(2))

        return wl

    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, new_id):
        self.__id = new_id

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, new_name):
        self.__name = new_name

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, new_url):
        self.__url = new_url

    @property
    def price(self):
        return self.__price

    @price.setter
    def price(self, new_price):
        self.__price = new_price

    def get_html(self):
        if not self.__html:
            self.__html = geizhals.core.send_request(self.__url)

    # Get the current price of a certain wishlist
    def get_current_price(self):
        """Get the current price of a wishlist from Geizhals"""
        self.get_html()
        price = geizhals.core.parse_wishlist_price(self.__html)

        # Parse price so that it's a proper comma value (no `,--`)
        pattern = "([0-9]+)\.([0-9]+|[-]+)"
        pattern_dash = "([0-9]+)\.([-]+)"

        if re.match(pattern, price):
            if re.match(pattern_dash, price):
                price = float(re.search(pattern_dash, price).group(1))
        else:
            raise ValueError("Couldn't parse price!")

        return float(price)

    def get_current_name(self):
        """Get the current name of a wishlist from Geizhals"""
        self.get_html()

        name = geizhals.core.parse_wishlist_name(self.__html)
        return name

    def get_current_id(self):
        self.get_html()

        id = geizhals.core.parse_wishlist_id(self.__html)


    def get_wishlist_products(self):
        raise NotImplementedError("get_wishlist_products is not implemented yet")
