# -*- coding: utf-8 -*-
from enum import Enum


class EntityType(Enum):
    WISHLIST = 1
    PRODUCT = 2

    @staticmethod
    def get_type_article_name(entity_type):
        if entity_type == EntityType.WISHLIST:
            return dict(article="die", name="Wunschliste")
        elif entity_type == EntityType.PRODUCT:
            return dict(article="das", name="Produkt")
        else:
            raise ValueError("No such entity type '{}'!".format(entity_type))
