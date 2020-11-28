import warnings

from ..api import API, MyGeotabException, AuthenticationException, Credentials

warnings.warn(
    "Please use `from mygeotab import X`. Imports using `from mygeotab.py3 import X` have been deprecated.",
    DeprecationWarning,
)

__all__ = ["API", "Credentials", "MyGeotabException", "AuthenticationException"]
