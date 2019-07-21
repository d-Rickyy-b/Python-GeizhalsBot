import random
import logging

logger = logging.getLogger(__name__)


class GeizhalsStateHandler(object):
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GeizhalsStateHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self, use_proxies=False, proxies=None):
        # Make sure that the object does not get overwritten each time the constructor get's called
        if GeizhalsStateHandler._initialized:
            return
        self.use_proxies = use_proxies
        self.proxies = proxies
        self.selected_proxy = self._get_next_proxy()
        GeizhalsStateHandler._initialized = True

    def _get_next_proxy(self):
        if self.use_proxies and self.proxies is not None:
            proxy = random.choice(self.proxies)
            self.selected_proxy = proxy
            return proxy
        else:
            logger.warning("No proxies configured!")
            return None

    def get_next_proxy(self):
        logger.debug("Choosing new proxy.")
        current_proxy = self.selected_proxy

        while True:
            proxy = self._get_next_proxy()
            if current_proxy != proxy:
                break
            if len(self.proxies) <= 1:
                logger.warning("Less than two proxies configured, using the same proxy again!")

        logger.debug("Selected '{}' as new proxy".format(proxy))
        return proxy
