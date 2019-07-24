# -*- coding: utf-8 -*-
import html
import logging

import requests
from pyquery import PyQuery
from requests.exceptions import ProxyError

from geizhals.entity import EntityType
from geizhals.exceptions import HTTPLimitedException
from geizhals.state_handler import GeizhalsStateHandler

logger = logging.getLogger(__name__)
useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) " \
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 " \
            "Safari/537.36"


def send_request(url):
    logger.debug("Requesting url '{}'!".format(url))
    statehandler = GeizhalsStateHandler()

    successful_connection = False
    r = None

    for i in range(3):
        logger.debug("Trying to download site {}/3".format(i + 1))
        if statehandler.use_proxies:
            proxy = statehandler.get_next_proxy()
            logger.debug("Using proxy: '{}'".format(proxy))
            proxies = dict(http=proxy, https=proxy)
        else:
            proxy = None
            proxies = None

        try:
            r = requests.get(url, headers={'User-Agent': useragent}, proxies=proxies, timeout=4)
        except ProxyError as e:
            logger.warning("An error using the proxy '{}' occurred: {}. Trying another proxy if possible!".format(proxy, e))
            continue

        if r.status_code == 429:
            logger.error("Geizhals blocked us from sending that many requests! Please consider adding request limits!")
            if statehandler.use_proxies:
                proxy = statehandler.get_next_proxy()
                logger.info("Switching proxy to '{}".format(proxy))
            continue
        elif r.status_code == 200:
            successful_connection = True
            break

    if not successful_connection:
        raise HTTPLimitedException("Geizhals blocked us temporarily!")

    html_str = r.content.decode()
    logger.debug("HTML content length: {} - status code: {}".format(len(html_str), r.status_code))
    html_str = html.unescape(html_str)
    return html_str


def parse_html(html_str, selector):
    pq = PyQuery(html_str)
    return pq(selector).text()


def parse_entity_price(html_str, entity_type):
    if entity_type == EntityType.WISHLIST:
        selector = "div.wishlist_sum_area span.gh_price span.gh_price > span.gh_price"
    elif entity_type == EntityType.PRODUCT:
        selector = "div#offer__price-0 span.gh_price"
    else:
        raise ValueError("The given type {} is unknown!".format(entity_type))

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
        raise ValueError("The given type {} is unknown!".format(entity_type))

    name = parse_html(html_str, selector)

    # Temporary fix for new Geizhals pages such as https://geizhals.de/sony-ht-rt3-schwarz-a1400003.html
    if name == "" and entity_type == EntityType.PRODUCT:
        name = parse_html(html_str, "#productpage__headline")

    # If name is still empty, raise error
    if name == "":
        raise ValueError("Name cannot be parsed!")

    return name
