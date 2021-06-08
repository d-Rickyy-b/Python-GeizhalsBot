# -*- coding: utf-8 -*-
from enum import Enum


class State(Enum):

    SEND_LINK = 0
    SEND_WL_LINK = 1
    SEND_P_LINK = 2
    IDLE = 3
