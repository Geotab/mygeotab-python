# -*- coding: utf-8 -*-

__title__ = "mygeotab-python"
__author__ = "Aaron Toth"

from importlib_metadata import PackageNotFoundError, version

try:
    VERSION = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    try:
        from .version import version as VERSION  # noqa
    except ImportError:  # pragma: no cover
        raise ImportError("Failed to get the version")
__version__ = VERSION

from .api import API, AsyncAPI, Credentials, server_call, server_call_async
from .exceptions import (AuthenticationException, MyGeotabException,
                         TimeoutException)

__all__ = [
    "API",
    "AsyncAPI",
    "Credentials",
    "MyGeotabException",
    "AuthenticationException",
    "TimeoutException",
    "server_call",
    "server_call_async",
]
