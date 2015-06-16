# -*- coding: utf-8 -*-

from datetime import datetime

import pytz


def get_utc_date(date):
    utc = pytz.utc
    if not date.tzinfo:
        date = utc.localize(date)
    return date.astimezone(utc)


def date_to_iso_str(date):
    date = get_utc_date(date)
    return date.replace(tzinfo=None).isoformat() + 'Z'


def parse_date(iso_date):
    """
    Parses an ISO 8601 date string into a datetime object

    :param iso_date: The date string
    :return: The datetime object which represents the ISO 8601 string
    """
    return datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%S.%fZ")
