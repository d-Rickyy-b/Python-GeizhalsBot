"""User entity data model"""


# -*- coding: utf-8 -*-


class User(object):

    def __init__(self, user_id: int, first_name: str, last_name: str, username: str, lang_code: str):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name or ""
        self.username = username
        self.lang_code = lang_code or "de-DE"
