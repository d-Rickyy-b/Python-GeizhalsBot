# -*- coding: utf-8 -*-


class UserState(object):
    def __init__(self, user_id, state):
        self.__user_id = user_id
        self.__state = state

    def user_id(self):
        return self.__user_id

    def state(self):
        return self.__state
