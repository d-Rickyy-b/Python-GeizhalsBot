# -*- coding: utf-8 -*-
import logging
from queue import Queue, Empty

logger = logging.getLogger(__name__)


class Ringbuffer(object):

    def __init__(self, elements):
        self.queue = Queue()
        for element in elements:
            self.queue.put(element)

    def next(self):
        try:
            element = self.queue.get(block=False)
            self.queue.put(element)
        except Empty:
            logger.error("Queue is empty. Returning None!")
            return None

        return element

    def __len__(self):
        return self.queue.qsize()
