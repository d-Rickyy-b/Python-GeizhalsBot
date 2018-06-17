# -*- coding: utf-8 -*-

from telegram.ext import BaseFilter


class _FilterNew(BaseFilter):
    def filter(self, message):
        commands = ["Neuer Preisagent"]
        return message.text in commands


class _FilterShow(BaseFilter):
    def filter(self, message):
        commands = ["Meine Preisagenten"]
        return message.text in commands


new_filter = _FilterNew()
show_filter = _FilterShow()
