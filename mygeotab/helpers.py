# -*- coding: utf-8 -*-

from datetime import datetime


def date_from_iso(date):
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")