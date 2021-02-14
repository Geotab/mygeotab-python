"""
mygeotab.serializers
~~~~~~~~~~~~~~~~~~~~

JSON serialization and deserialization helper objects for the MyGeotab API.
"""

import re

import arrow
import rapidjson

from mygeotab import dates

DATETIME_MODE = rapidjson.DM_SHIFT_TO_UTC | rapidjson.DM_ISO8601
DATETIME_REGEX = re.compile(r"^\d{4}\-\d{2}\-\d{2}")


def json_serialize(obj):
    return rapidjson.dumps(obj, default=object_serializer)


def json_deserialize(json_str):
    return rapidjson.loads(json_str, datetime_mode=DATETIME_MODE)


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
        if isinstance(val, str) and DATETIME_REGEX.search(val):
            try:
                obj[key] = dates.localize_datetime(arrow.get(val).datetime)
            except (ValueError, arrow.parser.ParserError):
                obj[key] = val
    return obj
