# -*- coding: utf-8 -*-
import html
import logging
import urllib.request
from geizhals.entity import EntityType

from pyquery import PyQuery

logger = logging.getLogger(__name__)
useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) " \
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 " \
            "Safari/537.36"


def send_request(url):
    logger.debug("Requesting url '{}'!".format(url))

    req = urllib.request.Request(
        url,
        data=None,
        headers={'User-Agent': useragent}
    )

    f = urllib.request.urlopen(req)
    html_str = f.read().decode('utf-8')
    html_str = html.unescape(html_str)
    return html_str


def parse_html(html_str, selector):
    pq = PyQuery(html_str)
    return pq(selector).text()


def parse_entity_price(html_str, entity_type):
    if entity_type == EntityType.WISHLIST:
        selector = "div.productlist__footer-cell span.gh_price"
    elif entity_type == EntityType.PRODUCT:
        selector = "div#offer__price-0 span.gh_price"
    else:
        raise ValueError("The given type is unknown!")

    price = parse_html(html_str, selector)
    price = price[2:]  # Cut off the '€ ' before the real price
    price = price.replace(',', '.')
    return price


def parse_entity_name(html_str, entity_type):
    if entity_type == EntityType.WISHLIST:
        selector = "h1.gh_listtitle"
    elif entity_type == EntityType.PRODUCT:
        selector = "div#gh_artbox span[itemprop='name']"
    else:
        raise ValueError("The given type is unknown!")

    name = parse_html(html_str, selector)
    return name
