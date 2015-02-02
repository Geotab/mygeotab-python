# -*- coding: utf-8 -*-

from datetime import datetime


def parse_date(iso_date):
    """
    Parses an ISO 8601 date string into a datetime object

    :param iso_date: The date string
    :return: The datetime object which represents the ISO 8601 string
    """
    return datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%S.%fZ")