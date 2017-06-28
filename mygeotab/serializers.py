# -*- coding: utf-8 -*-

"""
mygeotab.serializers
~~~~~~~~~~~~~~~~~~~~

JSON serialization and deserialization helper objects for the MyGeotab API.
"""

import re

import six
from dateutil import parser

from mygeotab import dates

DATETIME_REGEX = re.compile(r'^\d{4}\-\d{2}\-\d{2}')


def object_serializer(obj):
    """Helper to serialize a field into a compatible MyGeotab object.

    :param obj: The object.
    """
    return dates.format_iso_datetime(obj) if hasattr(obj, 'isoformat') else obj


def object_deserializer(obj):
    """Helper to deserialize a raw result dict into a proper dict.

    :param obj: The dict.
    """
    for key, val in obj.items():
        if isinstance(val, six.string_types) and DATETIME_REGEX.search(val):
            try:
                obj[key] = dates.localize_datetime(parser.parse(val))
            except ValueError:
                obj[key] = val
    return obj
