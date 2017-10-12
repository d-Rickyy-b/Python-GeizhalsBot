class Wishlist(object):

    def __init__(self, id, name, url, price):
        self.__id = int(id)
        self.__name = str(name)
        self.__url = str(url)
        self.__price = float(price)

    def id(self):
        return self.__id

    def name(self):
        return self.__name

    def url(self):
        return self.__url

    def price(self):
        return self.__price

    def update_price(self, new_price):
        self.__price = new_price