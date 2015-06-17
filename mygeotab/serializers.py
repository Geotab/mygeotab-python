# -*- coding: utf-8 -*-

import re

import six
from dateutil import parser

import mygeotab.utils


def object_serializer(obj):
    return mygeotab.utils.date_to_iso_str(obj) if hasattr(obj, 'isoformat') else obj


def object_deserializer(obj):
    for k, v in obj.items():
        lower_k = k.lower()
        if isinstance(v, six.string_types) and (
            'date' in lower_k or 'time' in lower_k or 'active' in lower_k) and re.search(
                r'^\d{4}\-\d{2}\-\d{2}', v):
            # noinspection PyBroadException
            try:
                obj[k] = parser.parse(v)
            except:
                pass
    return obj

