# -*- coding: utf-8 -*-

from telegram.ext import BaseFilter


class OwnFilters(object):
    class _FilterNewList(BaseFilter):
        def filter(self, message):
            return message.text.startswith("Neue Liste")

    new_list = _FilterNewList()

    class _FilterDeleteList(BaseFilter):
        def filter(self, message):
            return message.text.startswith("Liste löschen")

    delete_list = _FilterDeleteList()

    class _FilterMyLists(BaseFilter):
        def filter(self, message):
            return message.text.startswith("Meine Wunschlisten")

    my_lists = _FilterMyLists()
