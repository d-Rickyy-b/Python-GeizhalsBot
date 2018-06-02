# -*- coding: utf-8 -*-

from telegram.ext import BaseFilter


class _FilterNewList(BaseFilter):
    def filter(self, message):
        return message.text.startswith("Neue Liste")


new_list_filter = _FilterNewList()


class _FilterDeleteList(BaseFilter):
    def filter(self, message):
        return message.text.startswith("Liste löschen")


delete_list_filter = _FilterDeleteList()


class _FilterMyLists(BaseFilter):
    def filter(self, message):
        return message.text.startswith("Meine Wunschlisten")


my_lists_filter = _FilterMyLists()
