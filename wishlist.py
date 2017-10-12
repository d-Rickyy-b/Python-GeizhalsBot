class Wishlist(object):

    def __init__(self, name, url, price):
        self.__name = str(name)
        self.__url = str(url)
        self.__price = str(price)

    def name(self):
        return self.__name

    def url(self):
        return self.__url

    def price(self):
        return self.__price
