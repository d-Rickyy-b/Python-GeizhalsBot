# -*- coding: utf-8 -*-


class Day(object):

    def __init__(self, date):
        self.date = date
        self.prices = []
        self.lowest_price = None
        self.highest_price = None

    def add_price(self, price):
        self.prices.append(price)

    def get_best_price(self):
        lowest_price = 999999999
        for price in self.prices:
            if price.price < lowest_price:
                lowest_price = price.price
        self.lowest_price = lowest_price
        return lowest_price

    def get_worst_price(self):
        highest_price = 0
        for price in self.prices:
            if price.price > highest_price:
                highest_price = price.price
        self.highest_price = highest_price
        return highest_price

    def __hash__(self):
        return self.date
