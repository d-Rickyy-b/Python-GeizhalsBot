"""User entity data model"""


# -*- coding: utf-8 -*-


class User(object):

    def __init__(self, id: int, first_name: str, username: str, lang_code: str):
        if lang_code is None:
            lang_code = "de-DE"

        self.id = id
        self.first_name = first_name
        self.username = username
        self.lang_code = lang_code
