# -*- coding: utf-8 -*-

import re

import six
from dateutil import parser

import mygeotab.dates

datetime_regex = re.compile(r'^\d{4}\-\d{2}\-\d{2}')


def object_serializer(obj):
    return mygeotab.dates.format_iso_datetime(obj) if hasattr(obj, 'isoformat') else obj


def object_deserializer(obj):
    for k, v in obj.items():
        if isinstance(v, six.string_types) and datetime_regex.search(v):
            try:
                obj[k] = parser.parse(v)
            except ValueError:
                obj[k] = v
    return obj
