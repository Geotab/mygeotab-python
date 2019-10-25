# -*- coding: utf-8 -*-

"""
mygeotab.serializers
~~~~~~~~~~~~~~~~~~~~

JSON serialization and deserialization helper objects for the MyGeotab API.
"""

import re

import arrow
import six

use_rapidjson = False
try:
    import rapidjson

    DATETIME_MODE = rapidjson.DM_SHIFT_TO_UTC | rapidjson.DM_ISO8601

    use_rapidjson = True
except ImportError:
    pass
import json

from mygeotab import dates

DATETIME_REGEX = re.compile(r"^\d{4}\-\d{2}\-\d{2}")


def json_serialize(obj):
    if use_rapidjson:
        return rapidjson.dumps(obj, default=object_serializer)
    return json.dumps(obj, default=object_serializer, separators=(",", ":"))


def json_deserialize(json_str):
    if use_rapidjson:
        return rapidjson.loads(json_str, datetime_mode=DATETIME_MODE)
    return json.loads(json_str, object_hook=object_deserializer)


def object_serializer(obj):
    """Helper to serialize a field into a compatible MyGeotab object.

    :param obj: The object.
    """
    return dates.format_iso_datetime(obj) if hasattr(obj, "isoformat") else obj


def object_deserializer(obj):
    """Helper to deserialize a raw result dict into a proper dict.

    :param obj: The dict.
    """
    for key, val in obj.items():
        if isinstance(val, six.string_types) and DATETIME_REGEX.search(val):
            try:
                obj[key] = dates.localize_datetime(arrow.get(val).datetime)
            except (ValueError, arrow.parser.ParserError):
                obj[key] = val
    return obj
