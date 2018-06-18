# -*- coding: utf-8 -*-

__title__ = 'mygeotab-python'
__author__ = 'Aaron Toth'
__version__ = '0.6.2'

from .api import Credentials
from .exceptions import MyGeotabException, AuthenticationException, TimeoutException

try:
    from .py3.api_async import API
except (SyntaxError, ImportError):
    from .api import API

__all__ = ['API', 'Credentials', 'MyGeotabException', 'AuthenticationException', 'TimeoutException']
