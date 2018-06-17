# -*- coding: utf-8 -*-
import html
import logging
import urllib.request

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


def parse_wishlist_price(html_str):
    selector = "div.productlist__footer-cell span.gh_price"
    price = parse_html(html_str, selector)
    price = price[2:]  # Cut off the '€ ' before the real price
    price = price.replace(',', '.')
    return price


def parse_wishlist_name(html_str):
    selector = "h1.gh_listtitle"
    name = parse_html(html_str, selector)
    return name


def parse_product_price(html_str):
    # TODO Add selector
    selector = ""
    price = parse_html(html_str, selector)
    return price


def parse_product_name(html_str):
    # TODO Add selector
    selector = ""
    name = parse_html(html_str, selector)
    return name
