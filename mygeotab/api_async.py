# -*- coding: utf-8 -*-

"""
mygeotab.api_async
~~~~~~~~~~~~~~~~~~

Backwards compatibility module. All async functionality is now in api.py.
The API class now supports both sync and async operations.
"""

from .api import API, server_call_async
from .http import DEFAULT_TIMEOUT

__all__ = ["API", "server_call_async", "DEFAULT_TIMEOUT"]
