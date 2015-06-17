# -*- coding: utf-8 -*-

from datetime import datetime

import pytz
from tzlocal import get_localzone


def get_utc_date(date):
    if not date.tzinfo:
        date = pytz.utc.localize(date)
    return date.astimezone(pytz.utc)

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


def localize_date(date):
    """
    Converts a naive or UTC-localized date into the current machine's timezone

    :param date: The datetime object
    :return: The datetime object, localized in the machine's timezone
    """
    localzone = get_localzone()
    if not date.tzinfo:
        return localzone.localize(date)
    else:
        return date.astimezone(localzone)
