# -*- coding: utf-8 -*-


class Product(object):
    def __init__(self, id, name, url, price):
        self.__id = int(id)
        self.__name = str(name)
        self.__url = str(url)
        self.__price = float(price)
