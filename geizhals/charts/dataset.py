# -*- coding: utf-8 -*-
from datetime import date
from .price import Price
from .day import Day
import requests
import json


class Dataset(object):

    def __init__(self, product_name):
        self.days = []
        self.product_name = product_name

    def add_price(self, price, timestamp):
        # find correct day to add to
        p = Price(price, timestamp)
        timestamp_date = date.fromtimestamp(timestamp)
        for day in self.days:
            if day.date == timestamp_date:
                day.add_price(p)
                return

        new_day = Day(timestamp_date)
        new_day.add_price(p)
        self.days.append(new_day)

    def get_best_price(self):
        lowest_price = 999999999
        for day in self.days:
            day_best_price = day.get_best_price()
            if lowest_price > day_best_price:
                lowest_price = day_best_price

        return lowest_price

    def get_worst_price(self):
        highest_price = 0
        for day in self.days:
            day_worst_price = day.get_worst_price()
            if highest_price < day_worst_price:
                highest_price = day_worst_price

        return highest_price

    def get_chart(self):
        labels = []
        prices = []
        for day in self.days:
            labels.append(str(day.date))
            prices.append(day.get_best_price())
        labels.reverse()
        prices.reverse()

        best_price = self.get_best_price()
        worst_price = self.get_worst_price()
        diff = worst_price - best_price

        data = dict(labels=labels, datasets=[dict(label=self.product_name, data=prices)])
        req_data = dict(type="line", data=data,
                        options=dict(
                            legend=dict(display=False),
                            title=dict(display=True, text=self.product_name),
                            scales=dict(yAxes=[dict(ticks=dict(suggestedMin=best_price - 2 * diff, suggestedMax=worst_price + diff / 2))],
                                        xAxes=[dict(type="time")])
                        )
                        )
        chart_query = json.dumps(req_data)
        response = requests.post(url="https://quickchart.io/chart", json=dict(c=chart_query, backgroundColor="white"))
        return response.content
