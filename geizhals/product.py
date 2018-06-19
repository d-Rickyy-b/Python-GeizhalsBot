# -*- coding: utf-8 -*-

import re

import geizhals.core
import geizhals.exceptions


class Product(object):
    url_pattern = "https:\/\/geizhals\.(de|at|eu)\/[0-9a-zA-Z\-]*a([0-9]+).html"
    type = "p"

    def __init__(self, id, name, url, price):
        self.__html = None
        self.__id = int(id)
        self.__name = str(name)
        self.__url = str(url)
        self.__price = float(price)

    @staticmethod
    def from_url(url):
        if not re.match(Product.url_pattern, url):
            raise geizhals.exceptions.InvalidWishlistURLException

        p = Product(0, "", url, 0)
        p.price = p.get_current_price()
        p.name = p.get_current_name()
        p.id = int(re.search(Product.url_pattern, url).group(2))

        return p

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
        """Check if html for product is already downloaded - if not download html and save in wishlist.__html"""
        if not self.__html:
            self.__html = geizhals.core.send_request(self.__url)

    def get_current_price(self):
        """Get the current price of a wishlist from Geizhals"""
        self.get_html()
        self.get_current_name()
        price = geizhals.core.parse_product_price(self.__html)

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

        name = geizhals.core.parse_product_name(self.__html)

        return name
