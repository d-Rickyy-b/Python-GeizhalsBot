# -*- coding: utf-8 -*-

import geizhals.core


class Product(object):
    def __init__(self, id, name, url, price):
        self.__html = None
        self.__id = int(id)
        self.__name = str(name)
        self.__url = str(url)
        self.__price = float(price)

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
